# apps/credit/ml_scoring.py
import joblib
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / 'ml_model' / 'models'

_model = None
_feature_names = None


def load_models():
    """Загружает только модель и список признаков"""
    global _model, _feature_names
    
    if _model is None:
        try:
            # Загружаем модель
            _model = joblib.load(MODELS_DIR / 'xgboost_bank_v2.pkl')
            logger.info("✅ Модель загружена")
            
            # Загружаем список признаков
            try:
                with open(MODELS_DIR / 'feature_names_bank.pkl', 'rb') as f:
                    _feature_names = pickle.load(f)
                logger.info(f"✅ Загружено {len(_feature_names)} признаков")
            except:
                logger.warning("⚠️ feature_names_bank.pkl не найден, создаем стандартный список")
                _feature_names = [
                    'loan_amnt', 'installment', 'annual_inc', 'dti',
                    'delinq_2yrs', 'acc_now_delinq', 'pub_rec',
                    'pub_rec_bankruptcies', 'collections_12_mths_ex_med',
                    'revol_util', 'bc_util', 'total_bal_ex_mort',
                    'total_acc', 'tot_hi_cred_lim',
                    'emp_length', 'home_ownership_encoded', 'credit_history_years',
                    'inq_last_6mths', 'mths_since_recent_inq', 'percent_bc_gt_75'
                ]
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    return _model, _feature_names


def preprocess_for_scoring(client_data):
    """Преобразует ClientData в формат для модели"""
    
    # Базовые признаки
    data = {
        'loan_amnt': float(client_data.loan_amnt) if client_data.loan_amnt else 0,
        'installment': float(client_data.installment) if client_data.installment else 0,
        'annual_inc': float(client_data.annual_inc) if client_data.annual_inc else 0,
        'dti': float(client_data.dti) if client_data.dti else 0,
        'delinq_2yrs': client_data.delinq_2yrs or 0,
        'acc_now_delinq': client_data.acc_now_delinq or 0,
        'pub_rec': client_data.pub_rec or 0,
        'pub_rec_bankruptcies': client_data.pub_rec_bankruptcies or 0,
        'collections_12_mths_ex_med': client_data.collections_12_mths_ex_med or 0,
        'revol_util': float(client_data.revol_util) if client_data.revol_util else 0,
        'bc_util': float(client_data.bc_util) if client_data.bc_util else 0,
        'total_bal_ex_mort': float(client_data.total_bal_ex_mort) if client_data.total_bal_ex_mort else 0,
        'total_acc': client_data.total_acc or 0,
        'tot_hi_cred_lim': float(client_data.tot_hi_cred_lim) if client_data.tot_hi_cred_lim else 0,
        'emp_length': client_data.emp_length or 0,
        'inq_last_6mths': client_data.inq_last_6mths or 0,
        'mths_since_recent_inq': client_data.mths_since_recent_inq or 0,
        'percent_bc_gt_75': float(client_data.percent_bc_gt_75) if client_data.percent_bc_gt_75 else 0,
    }
    
    # Обработка home_ownership
    home_map = {'RENT': 0, 'MORTGAGE': 1, 'OWN': 2, 'OTHER': 3}
    data['home_ownership_encoded'] = home_map.get(client_data.home_ownership, 3)
    
    # Обработка earliest_cr_line → credit_history_years
    if client_data.earliest_cr_line:
        try:
            year = client_data.earliest_cr_line.year
            data['credit_history_years'] = 2018 - year
        except:
            data['credit_history_years'] = 0
    else:
        data['credit_history_years'] = 0
    
    # Создаем DataFrame
    df = pd.DataFrame([data])
    
    return df


def predict_application(application):
    """
    Выполняет скоринг для кредитной заявки
    """
    try:
        model, feature_names = load_models()
        
        # Получаем данные клиента
        client_data = application.client_data
        
        # Предобработка
        df = preprocess_for_scoring(client_data)
        
        # Убеждаемся, что все признаки есть в правильном порядке
        for feature in feature_names:
            if feature not in df.columns:
                df[feature] = 0
        
        df = df[feature_names]
        
        # Предсказание
        # Обрабатываем возможную ошибку use_label_encoder
        try:
            proba = model.predict_proba(df)[0, 1]
        except AttributeError:
            if hasattr(model, 'use_label_encoder'):
                model.use_label_encoder = False
                proba = model.predict_proba(df)[0, 1]
            else:
                raise
        
        # Расчет скорингового балла
        T1 = 0.3
        T2 = 0.7
        Factor = 50
        Offset = 600
        
        odds = (1 - proba) / proba if proba > 0 else 1000
        score = int(Offset + Factor * np.log(odds))
        score = max(0, min(1000, score))
        
        # Решение
        if proba < T1:
            decision = "AUTO_APPROVE"
            decision_ru = "Автоодобрение"
        elif proba > T2:
            decision = "AUTO_REJECT"
            decision_ru = "Автоотказ"
        else:
            decision = "MANUAL_REVIEW"
            decision_ru = "Ручная проверка"
        
        logger.info(f"Скоринг: PD={proba:.2%}, Score={score}, Decision={decision}")
        
        return {
            'probability': proba,
            'score': score,
            'decision': decision,
            'decision_ru': decision_ru,
            'is_bad': int(proba > 0.5),
        }
        
    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        raise


def get_shap_factors(application, top_n=5):
    """SHAP временно отключен"""
    return []