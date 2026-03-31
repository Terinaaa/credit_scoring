# apps/scoring/ml_service.py
import joblib
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Подавляем предупреждения
warnings.filterwarnings('ignore')

# SHAP временно отключен - импортируем заглушку
try:
    import shap
except ImportError:
    # Создаем заглушку для shap
    class ShapStub:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
        def TreeExplainer(self, *args, **kwargs):
            return ShapStub()
    shap = ShapStub()

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / 'ml_model' / 'models'

# Глобальные переменные для кеширования
_model = None
_imputer = None
_score_params = None
_explainer = None
_feature_names = None


def load_models():
    """Загружает все компоненты модели"""
    global _model, _imputer, _score_params, _explainer, _feature_names
    
    if _model is None:
        try:
            # Загружаем модель
            _model = joblib.load(MODELS_DIR / 'xgboost_bank_v2.pkl')
            
            # Загружаем imputer (если есть)
            try:
                _imputer = joblib.load(MODELS_DIR / 'imputer_bank.pkl')
            except:
                _imputer = None
            
            # Загружаем параметры скоринга (если есть)
            try:
                with open(MODELS_DIR / 'score_params.pkl', 'rb') as f:
                    _score_params = joblib.load(f)
            except:
                _score_params = {
                    'T1': 0.3,
                    'T2': 0.7,
                    'Factor': 50,
                    'Offset': 600,
                    'score_T1': 650,
                    'score_T2': 350
                }
            
            # Загружаем список признаков
            try:
                with open(MODELS_DIR / 'feature_names_bank.pkl', 'rb') as f:
                    _feature_names = pickle.load(f)
            except:
                _feature_names = None
            
            # SHAP объяснитель (заглушка)
            _explainer = shap.TreeExplainer(_model) if hasattr(shap, 'TreeExplainer') else None
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise
    
    return _model, _imputer, _score_params, _explainer


def preprocess_input(form_data):
    """Преобразует данные из формы в формат модели"""
    df = pd.DataFrame([form_data])
    
    # 1. emp_length → извлекаем число лет стажа
    if 'emp_length' in df.columns:
        df['emp_length'] = (
            df['emp_length']
            .astype(str)
            .str.extract('(\d+)')[0]
            .astype(float)
        )
    
    # 2. home_ownership → кодируем как числа
    if 'home_ownership' in df.columns:
        home_map = {'RENT': 0, 'MORTGAGE': 1, 'OWN': 2, 'OTHER': 3}
        df['home_ownership'] = df['home_ownership'].map(home_map).fillna(3)
    
    # 3. earliest_cr_line → возраст кредитной истории
    if 'earliest_cr_line' in df.columns:
        df['earliest_cr_year'] = pd.to_datetime(
            df['earliest_cr_line'], errors='coerce'
        ).dt.year
        df['credit_history_years'] = 2018 - df['earliest_cr_year']
        df = df.drop(columns=['earliest_cr_line', 'earliest_cr_year'], errors='ignore')
    
    # 4. revol_util, bc_util, percent_bc_gt_75 → убираем %
    for col in ['revol_util', 'bc_util', 'percent_bc_gt_75']:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace('%', '', regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Заполняем пропуски
    df = df.fillna(0)
    
    return df


def predict(form_data):
    """Полный цикл предсказания"""
    
    # Загружаем модели
    model, imputer, score_params, explainer = load_models()
    
    # Предобработка
    X = preprocess_input(form_data)
    
    # Получаем список признаков модели
    try:
        expected_columns = model.get_booster().feature_names
    except:
        # Если не можем получить из модели, используем сохраненный список
        expected_columns = _feature_names or [
            'loan_amnt', 'installment', 'annual_inc', 'dti',
            'delinq_2yrs', 'acc_now_delinq', 'pub_rec',
            'pub_rec_bankruptcies', 'collections_12_mths_ex_med',
            'revol_util', 'bc_util', 'total_bal_ex_mort',
            'total_acc', 'tot_hi_cred_lim',
            'emp_length', 'home_ownership_encoded', 'credit_history_years',
            'inq_last_6mths', 'mths_since_recent_inq', 'percent_bc_gt_75'
        ]
    
    # Убеждаемся, что все нужные колонки есть
    for col in expected_columns:
        if col not in X.columns:
            X[col] = 0
    
    X = X[expected_columns]
    
    # Импутация (если есть imputer)
    if imputer is not None:
        try:
            X_imputed = pd.DataFrame(
                imputer.transform(X),
                columns=expected_columns
            )
        except:
            X_imputed = X.fillna(0)
    else:
        X_imputed = X.fillna(0)
    
    # Получаем вероятность дефолта
    try:
        pd_prob = model.predict_proba(X_imputed)[0, 1]
    except AttributeError:
        # Если ошибка с use_label_encoder
        if hasattr(model, 'use_label_encoder'):
            model.use_label_encoder = False
            pd_prob = model.predict_proba(X_imputed)[0, 1]
        else:
            raise
    
    # Трехзонная система
    T1 = score_params.get('T1', 0.3)
    T2 = score_params.get('T2', 0.7)
    
    if pd_prob < T1:
        decision = "AUTO_APPROVE"
        decision_ru = "Автоодобрение"
    elif pd_prob > T2:
        decision = "AUTO_REJECT"
        decision_ru = "Автоотказ"
    else:
        decision = "MANUAL_REVIEW"
        decision_ru = "Ручная проверка"
    
    # Перевод в Score
    Factor = score_params.get('Factor', 50)
    Offset = score_params.get('Offset', 600)
    odds = (1 - pd_prob) / pd_prob if pd_prob > 0 else 1000
    score = int(Offset + Factor * np.log(odds))
    score = max(0, min(1000, score))
    
    # SHAP объяснение (отключено)
    factors = []
    
    return {
        'probability': round(pd_prob * 100, 2),
        'probability_raw': float(pd_prob),
        'decision': decision,
        'decision_ru': decision_ru,
        'score': score,
        'factors': factors,
        'thresholds': {
            'T1': T1,
            'T2': T2,
            'score_T1': score_params.get('score_T1', int(Offset + Factor * np.log((1-0.3)/0.3))),
            'score_T2': score_params.get('score_T2', int(Offset + Factor * np.log((1-0.7)/0.7)))
        }
    }