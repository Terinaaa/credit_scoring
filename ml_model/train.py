"""
Полный скрипт для обучения модели кредитного скоринга
Можно запускать командой: python ml_model/train.py
"""

import numpy as np
import pandas as pd
import joblib
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

# создание необходимых папок
os.makedirs('ml_model/models', exist_ok=True)
os.makedirs('ml_model/data', exist_ok=True)

def create_target(status):
    """Создание бинарной целевой переменной"""
    if pd.isna(status):
        return None
    status = str(status)
    bad_statuses = ['Charged Off', 'Default', 'Late (31-120 days)', 
                    'Late (16-30 days)', 'Does not meet the credit policy. Status:Charged Off']
    if status in bad_statuses:
        return 1
    elif status == 'Fully Paid':
        return 0
    else:
        return None

def preprocess_features(X):
    """Предобработка признаков"""
    X_processed = X.copy()
    
    # обработка term
    if 'term' in X_processed.columns:
        X_processed['term'] = X_processed['term'].astype(str).str.extract('(\d+)').astype(float)
    
    # обработка процентных ставок
    for col in ['int_rate', 'revol_util']:
        if col in X_processed.columns:
            X_processed[col] = X_processed[col].astype(str).str.replace('%', '').astype(float)
    
    # обработка emp_length
    if 'emp_length' in X_processed.columns:
        def parse_emp_length(x):
            if pd.isna(x):
                return np.nan
            x = str(x)
            if '10+' in x:
                return 10
            elif '< 1' in x or '<1' in x:
                return 0
            else:
                num = ''.join(filter(str.isdigit, x))
                return float(num) if num else np.nan
        X_processed['emp_length'] = X_processed['emp_length'].apply(parse_emp_length)
    
    # кодирование категориальных признаков
    categorical_cols = ['grade', 'sub_grade', 'home_ownership', 'verification_status']
    for col in categorical_cols:
        if col in X_processed.columns:
            le = LabelEncoder()
            X_processed[f'{col}_encoded'] = le.fit_transform(X_processed[col].astype(str))
            X_processed.drop(col, axis=1, inplace=True)
    
    return X_processed

def load_and_prepare_data(filepath):
    """Загрузка и подготовка данных"""
    print(f"Загрузка данных из {filepath}...")
    df = pd.read_csv(filepath, compression='gzip', low_memory=False)
    print(f"Загружено {len(df)} записей")
    
    # создание целевой переменной
    print("Создание целевой переменной...")
    df['is_bad'] = df['loan_status'].apply(create_target)
    df_model = df.dropna(subset=['is_bad']).copy()
    print(f"После фильтрации: {len(df_model)} записей")
    print(f"Доля дефолтов: {df_model['is_bad'].mean():.2%}")
    
    # список признаков
    feature_columns = [
        'loan_amnt', 'term', 'int_rate', 'installment', 'grade', 'sub_grade',
        'emp_length', 'home_ownership', 'annual_inc', 'verification_status',
        'dti', 'delinq_2yrs', 'fico_range_low', 'fico_range_high',
        'inq_last_6mths', 'open_acc', 'pub_rec', 'revol_bal', 'revol_util',
        'total_acc', 'acc_now_delinq', 'mort_acc', 'pub_rec_bankruptcies',
        'bc_util', 'all_util', 'percent_bc_gt_75', 'num_actv_bc_tl',
        'num_il_tl', 'num_rev_accts', 'pct_tl_nvr_dlq', 'tot_hi_cred_lim',
        'total_bal_ex_mort', 'total_bc_limit', 'collections_12_mths_ex_med',
        'mo_sin_old_rev_tl_op', 'mths_since_recent_bc', 'mths_since_recent_inq'
    ]
    
    available_features = [col for col in feature_columns if col in df_model.columns]
    print(f"Используется {len(available_features)} признаков")
    
    X = df_model[available_features].copy()
    y = df_model['is_bad'].copy()
    
    return X, y

def train_model(X, y):
    """Обучение модели"""
    print("Предобработка признаков...")
    X_processed = preprocess_features(X)
    
    # Удаляем признаки с >50% пропусков
    missing_ratio = X_processed.isnull().sum() / len(X_processed)
    high_missing = missing_ratio[missing_ratio > 0.5].index.tolist()
    if high_missing:
        X_processed = X_processed.drop(columns=high_missing)
        print(f"Удалено {len(high_missing)} признаков с >50% пропусков")
    
    # Заполняем пропуски
    numeric_cols = X_processed.select_dtypes(include=[np.number]).columns.tolist()
    imputer = SimpleImputer(strategy='median')
    X_processed[numeric_cols] = imputer.fit_transform(X_processed[numeric_cols])
    
    # Разделение на train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Масштабирование
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Баланс классов
    scale_pos_weight = len(y_train[y_train==0]) / len(y_train[y_train==1])
    
    # Обучение модели с подбором параметров
    print("Подбор гиперпараметров...")
    xgb_model = xgb.XGBClassifier(
        objective='binary:logistic',
        random_state=42,
        n_jobs=-1,
        eval_metric='auc'
    )
    
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [100, 200],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0],
        'scale_pos_weight': [scale_pos_weight]
    }
    
    random_search = RandomizedSearchCV(
        xgb_model, param_distributions=param_grid,
        n_iter=10, scoring='roc_auc', cv=3,
        random_state=42, n_jobs=-1, verbose=1
    )
    
    random_search.fit(X_train_scaled, y_train)
    
    print(f"\nЛучшие параметры: {random_search.best_params_}")
    print(f"Лучший AUC на CV: {random_search.best_score_:.4f}")
    
    # Оценка на тесте
    best_model = random_search.best_estimator_
    y_pred_proba = best_model.predict_proba(X_test_scaled)[:, 1]
    test_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC на тесте: {test_auc:.4f}")
    
    return best_model, scaler, X_processed.columns.tolist()

def save_model(model, scaler, feature_names):
    """Сохранение модели и компонентов"""
    print("\nСохранение модели...")
    
    # Сохраняем модель
    joblib.dump(model, 'ml_model/models/xgboost_model.pkl')
    
    # Сохраняем скейлер
    joblib.dump(scaler, 'ml_model/models/scaler.pkl')
    
    # Сохраняем имена признаков
    with open('ml_model/models/feature_names.pkl', 'wb') as f:
        pickle.dump(feature_names, f)
    
    # Сохраняем версию и метаданные
    metadata = {
        'model_type': 'XGBoost',
        'features_count': len(feature_names),
        'features': feature_names
    }
    
    with open('ml_model/models/metadata.pkl', 'wb') as f:
        pickle.dump(metadata, f)
    
    print("Модель сохранена в ml_model/models/")

if __name__ == "__main__":
    # Укажите путь к вашему датасету
    data_path = "ml_model/data/accepted_2007_to_2018Q4.csv.gz"
    
    # Загружаем данные
    X, y = load_and_prepare_data(data_path)
    
    # Обучаем модель
    model, scaler, feature_names = train_model(X, y)
    
    # Сохраняем модель
    save_model(model, scaler, feature_names)
    
    print("\n✅ Обучение успешно завершено!")