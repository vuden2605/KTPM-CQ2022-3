"""
train_model_1h.py
Train model dự đoán UP/DOWN/NEUTRAL cho 1H tiếp theo
(Dùng label_1h từ CSV - based on abret_1h)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    precision_recall_fscore_support
)
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from datetime import datetime

# ============================================
# 1. LOAD DATA
# ============================================

print("=" * 70)
print("TRAIN MODEL 1H: PREDICT UP/DOWN/NEUTRAL FOR NEXT 1 HOUR")
print("=" * 70)

df = pd.read_csv('aligned_news_price_per_article_2025-12-01_to_2026-01-22.csv')

# Parse datetime
df['news_timestamp'] = pd.to_datetime(df['news_timestamp'])

# ===== SỬA: Kiểm tra xem CSV có label_1h chưa =====
if 'label_1h' not in df.columns:
    print("❌ Error: CSV missing 'label_1h' column!")
    print("   Run align_pipeline.py with updated code first!")
    import sys
    sys.exit(1)

# Filter out UNKNOWN labels (dùng label_1h từ CSV)
df = df[df['label_1h'].notna()].copy()
df = df[df['label_1h'] != 'UNKNOWN'].copy()

print(f"✓ Loaded {len(df)} samples")
print(f"  Date range: {df['news_timestamp'].min()} to {df['news_timestamp'].max()}")

# ============================================
# 2. FEATURE ENGINEERING (1H VERSION)
# ============================================

print("\n" + "=" * 70)
print("2. FEATURE ENGINEERING (1H TARGET)")
print("=" * 70)

# ===== SỬA: Thêm baseline_ret_1h nếu có trong CSV =====
feature_cols = [
    # Existing
    'sentiment_score',
    'breaking_score',
    'vol_pre_24h',
    'volume_pre_24h',
    
    # Baseline (check if exists)
    # 'baseline_ret_1h',  # Sẽ thêm sau if exists
    
    # NEW (11 features)
    'rsi_24h',
    'price_change_24h',
    'high_low_range_24h',
    'volume_ma_ratio',
    'market_cap_rank',
    'time_of_day',
    'day_of_week',
    'news_count_1h',
    'avg_sentiment_1h',
    'entity_importance',
    'keyword_strength',
]

if 'baseline_ret_1h' in df.columns:
    feature_cols.append('baseline_ret_1h')

# Derived
df['is_breaking_int'] = df['is_breaking'].astype(int)
df['sentiment_extreme'] = np.abs(df['sentiment_score'] - 0.5)

feature_cols.extend(['is_breaking_int', 'sentiment_extreme'])

# ===== SỬA: Dùng label_1h từ CSV (không tự tạo nữa) =====
target_col = 'label_1h'

# Drop rows có missing features
df_clean = df.dropna(subset=feature_cols + [target_col])

print(f"✓ Features selected: {feature_cols}")
print(f"✓ Target: {target_col} (from CSV, based on abret_1h)")
print(f"✓ Clean dataset: {len(df_clean)} samples")
print(f"  Label distribution:\n{df_clean[target_col].value_counts()}")

# ============================================
# 3. TRAIN/VAL/TEST SPLIT (STRATIFIED)
# ============================================

print("\n" + "=" * 70)
print("3. TRAIN/VAL/TEST SPLIT (STRATIFIED)")
print("=" * 70)

X = df_clean[feature_cols]
y = df_clean[target_col]

# Stratified split
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, stratify=y, random_state=42
)

X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.176, stratify=y_temp, random_state=42
)

# Map lại index
train_df = df_clean.loc[X_train.index]
val_df = df_clean.loc[X_val.index]
test_df = df_clean.loc[X_test.index]

print(f"Train set: {len(train_df)} samples")
print(f"Val set:   {len(val_df)} samples")
print(f"Test set:  {len(test_df)} samples")

print(f"\nLabel distribution:")
print(f"  Train: {dict(y_train.value_counts())}")
print(f"  Val:   {dict(y_val.value_counts())}")
print(f"  Test:  {dict(y_test.value_counts())}")

# ============================================
# 4. TRAIN MODEL
# ============================================

print("\n" + "=" * 70)
print("4. TRAINING MODEL (1H VERSION)")
print("=" * 70)

# Model 1: Random Forest
model_rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)

model_rf.fit(X_train, y_train)
print("✓ Random Forest trained")

# Model 2: Gradient Boosting
model_gb = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)

model_gb.fit(X_train, y_train)
print("✓ Gradient Boosting trained")
# Model 3: XGBoost
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder

# Encode labels (XGBoost cần numeric labels)
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_val_encoded = label_encoder.transform(y_val)
y_test_encoded = label_encoder.transform(y_test)

model_xgb = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='mlogloss',
    use_label_encoder=False
)

model_xgb.fit(X_train, y_train_encoded)
print("✓ XGBoost trained")
# ============================================
# 5. EVALUATE ON VALIDATION SET
# ============================================

print("\n" + "=" * 70)
print("5. VALIDATION SET PERFORMANCE")
print("=" * 70)

# Random Forest
y_val_pred_rf = model_rf.predict(X_val)
acc_val_rf = accuracy_score(y_val, y_val_pred_rf)
print(f"\nRandom Forest - Validation Accuracy: {acc_val_rf:.4f}")
print(classification_report(y_val, y_val_pred_rf, zero_division=0))

# Gradient Boosting
y_val_pred_gb = model_gb.predict(X_val)
acc_val_gb = accuracy_score(y_val, y_val_pred_gb)
print(f"\nGradient Boosting - Validation Accuracy: {acc_val_gb:.4f}")
print(classification_report(y_val, y_val_pred_gb, zero_division=0))
# XGBoost
y_val_pred_xgb_encoded = model_xgb.predict(X_val)
y_val_pred_xgb = label_encoder.inverse_transform(y_val_pred_xgb_encoded)
acc_val_xgb = accuracy_score(y_val, y_val_pred_xgb)
print(f"\nXGBoost - Validation Accuracy: {acc_val_xgb:.4f}")
print(classification_report(y_val, y_val_pred_xgb, zero_division=0))

# Chọn model tốt nhất
if acc_val_rf >= acc_val_gb:
    best_model = model_rf
    best_model_name = "Random Forest"
    best_acc = acc_val_rf
else:
    best_model = model_gb
    best_model_name = "Gradient Boosting"
    best_acc = acc_val_gb

print(f"\n✅ Selected model: {best_model_name} (acc: {best_acc:.4f})")

# ============================================
# 6. EVALUATE ON TEST SET
# ============================================

print("\n" + "=" * 70)
print("6. TEST SET PERFORMANCE (FINAL)")
print("=" * 70)

y_test_pred = best_model.predict(X_test)
y_test_proba = best_model.predict_proba(X_test)

acc_test = accuracy_score(y_test, y_test_pred)

print(f"\n{best_model_name} - Test Accuracy: {acc_test:.4f}")
print("\nClassification Report (Test Set):")
print(classification_report(y_test, y_test_pred, zero_division=0))

# Confusion Matrix
cm = confusion_matrix(y_test, y_test_pred, labels=['DOWN', 'NEUTRAL', 'UP'])

print("\nConfusion Matrix (Test Set):")
print("              Predicted")
print("               DOWN  NEUTRAL  UP")
print(f"Actual DOWN    {cm[0,0]:4d}  {cm[0,1]:4d}  {cm[0,2]:4d}")
print(f"       NEUTRAL {cm[1,0]:4d}  {cm[1,1]:4d}  {cm[1,2]:4d}")
print(f"       UP      {cm[2,0]:4d}  {cm[2,1]:4d}  {cm[2,2]:4d}")

# ============================================
# 7. FEATURE IMPORTANCE
# ============================================

print("\n" + "=" * 70)
print("7. FEATURE IMPORTANCE")
print("=" * 70)

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.to_string(index=False))

# ============================================
# 8. VISUALIZATIONS
# ============================================

print("\n" + "=" * 70)
print("8. CREATING VISUALIZATIONS...")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Confusion Matrix
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['DOWN', 'NEUTRAL', 'UP'],
            yticklabels=['DOWN', 'NEUTRAL', 'UP'],
            ax=axes[0, 0])
axes[0, 0].set_title(f'Confusion Matrix (Test Set - 1H)\nAccuracy: {acc_test:.2%}')
axes[0, 0].set_ylabel('Actual')
axes[0, 0].set_xlabel('Predicted')

# Plot 2: Feature Importance
axes[0, 1].barh(feature_importance['feature'], feature_importance['importance'])
axes[0, 1].set_xlabel('Importance')
axes[0, 1].set_title('Feature Importance (1H Model)')
axes[0, 1].invert_yaxis()
axes[0, 1].grid(alpha=0.3)

# Plot 3: Prediction distribution
test_label_dist = pd.Series(y_test_pred).value_counts()
axes[1, 0].bar(test_label_dist.index, test_label_dist.values, alpha=0.7, edgecolor='black')
axes[1, 0].set_xlabel('Predicted Label')
axes[1, 0].set_ylabel('Count')
axes[1, 0].set_title('Prediction Distribution (Test Set - 1H)')
axes[1, 0].grid(alpha=0.3)

# Plot 4: Accuracy by confidence
test_df_eval = test_df.copy()
test_df_eval['predicted'] = y_test_pred
test_df_eval['confidence'] = y_test_proba.max(axis=1)
test_df_eval['correct'] = (test_df_eval['predicted'] == test_df_eval[target_col])

bins = [0, 0.4, 0.6, 0.8, 1.0]
test_df_eval['conf_bin'] = pd.cut(test_df_eval['confidence'], bins=bins)
conf_acc = test_df_eval.groupby('conf_bin', observed=True)['correct'].mean()

axes[1, 1].bar(range(len(conf_acc)), conf_acc.values, alpha=0.7, edgecolor='black')
axes[1, 1].set_xticks(range(len(conf_acc)))
axes[1, 1].set_xticklabels([str(b) for b in conf_acc.index], rotation=45)
axes[1, 1].set_ylabel('Accuracy')
axes[1, 1].set_xlabel('Confidence Range')
axes[1, 1].set_title('Accuracy by Confidence (1H Model)')
axes[1, 1].grid(alpha=0.3)
axes[1, 1].axhline(acc_test, color='red', linestyle='--', label=f'Overall: {acc_test:.2%}')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('model_evaluation_1h.png', dpi=300, bbox_inches='tight')
print("✓ Saved: model_evaluation_1h.png")

plt.show()

# ============================================
# 9. SAVE MODEL
# ============================================

print("\n" + "=" * 70)
print("9. SAVING MODEL (1H VERSION)...")
print("=" * 70)

model_filename = f'model_1h_{best_model_name.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d")}.pkl'
joblib.dump(best_model, model_filename)
print(f"✓ Model saved: {model_filename}")

# Save metadata
feature_info = {
    'feature_cols': feature_cols,
    'model_name': best_model_name,
    'target': 'label_1h (based on abret_1h)',
    'test_accuracy': acc_test,
    'trained_date': datetime.now().isoformat(),
    'threshold': 0.3,  # ±0.3% for abret_1h
    'horizon': '1h',
    'uses_abnormal_return': 'baseline_ret_1h' in feature_cols
}

import json
with open('model_info_1h.json', 'w') as f:
    json.dump(feature_info, f, indent=2)
print("✓ Model info saved: model_info_1h.json")

# ============================================
# 10. SUMMARY
# ============================================

print("\n" + "=" * 70)
print("📊 MODEL 1H TRAINING SUMMARY")
print("=" * 70)

precision, recall, f1, support = precision_recall_fscore_support(
    y_test, y_test_pred, average=None, labels=['DOWN', 'NEUTRAL', 'UP'], zero_division=0
)

print(f"""
MODEL DETAILS:
--------------
Model: {best_model_name} (1H VERSION)
Target: label_1h (based on abret_1h, threshold ±0.3%)
Features: {len(feature_cols)} ({', '.join(feature_cols[:3])}...)
Training samples: {len(train_df)}
Test samples: {len(test_df)}

TEST SET PERFORMANCE:
---------------------
Overall Accuracy: {acc_test:.2%}

Per-class metrics:
  DOWN:    Precision {precision[0]:.2%}, Recall {recall[0]:.2%}, F1 {f1[0]:.2%}, Support {support[0]}
  NEUTRAL: Precision {precision[1]:.2%}, Recall {recall[1]:.2%}, F1 {f1[1]:.2%}, Support {support[1]}
  UP:      Precision {precision[2]:.2%}, Recall {recall[2]:.2%}, F1 {f1[2]:.2%}, Support {support[2]}

TOP 3 FEATURES:
---------------
1. {feature_importance.iloc[0]['feature']}: {feature_importance.iloc[0]['importance']:.4f}
2. {feature_importance.iloc[1]['feature']}: {feature_importance.iloc[1]['importance']:.4f}
3. {feature_importance.iloc[2]['feature']}: {feature_importance.iloc[2]['importance']:.4f}

SAVED FILES:
------------
- Model: {model_filename}
- Metadata: model_info_1h.json
- Visualization: model_evaluation_1h.png

CONCLUSION:
-----------
""")

if acc_test >= 0.70:
    print("✅ Model 1H đạt accuracy ≥70% → TỐT")
elif acc_test >= 0.60:
    print("⚠️ Model 1H accuracy 60-70% → CHẤP NHẬN ĐƯỢC")
else:
    print("❌ Model 1H accuracy <60% → CẦN TUNE")

print("\n✅ Model 1H training DONE!")
print("=" * 70)