"""
train_model_24h.py
Train model dự đoán UP/DOWN/NEUTRAL từ tin tức cho 24h
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
print("SUPERVISED LEARNING: TRAIN MODEL TO PREDICT UP/DOWN/NEUTRAL FOR NEXT 24 HOURS")
print("=" * 70)

df = pd.read_csv('aligned_news_price_per_article_2025-12-01_to_2026-01-22.csv')

# Parse datetime
df['news_timestamp'] = pd.to_datetime(df['news_timestamp'])

# Filter out UNKNOWN labels
df = df[df['label'] != 'UNKNOWN'].copy()

print(f"✓ Loaded {len(df)} samples")
print(f"  Date range: {df['news_timestamp'].min()} to {df['news_timestamp'].max()}")
print(f"  Label distribution:\n{df['label'].value_counts()}")

# ============================================
# 2. FEATURE ENGINEERING
# ============================================

print("\n" + "=" * 70)
print("2. FEATURE ENGINEERING")
print("=" * 70)

# Chọn features
feature_cols = [
    # Existing features (5)
    'sentiment_score',
    'breaking_score',
    'vol_pre_24h',
    'volume_pre_24h',
    'baseline_ret_24h',
    
    # ===== NEW FEATURES (11) =====
    # Technical indicators (4)
    'rsi_24h',
    'price_change_24h',
    'high_low_range_24h',
    'volume_ma_ratio',
    
    # Market context (3)
    'market_cap_rank',
    'time_of_day',
    'day_of_week',
    
    # News features (4)
    'news_count_1h',
    'avg_sentiment_1h',
    'entity_importance',
    'keyword_strength',
]

# Derived features (2)
df['is_breaking_int'] = df['is_breaking'].astype(int)
df['sentiment_extreme'] = np.abs(df['sentiment_score'] - 0.5)

feature_cols.extend(['is_breaking_int', 'sentiment_extreme'])

# ===== TOTAL: 5 + 11 + 2 = 18 features =====
# Target
target_col = 'label'

# Drop rows có missing features
df_clean = df.dropna(subset=feature_cols + [target_col])

print(f"✓ Features selected: {feature_cols}")
print(f"✓ Target: {target_col}")
print(f"✓ Clean dataset: {len(df_clean)} samples (dropped {len(df) - len(df_clean)} rows with missing values)")

# ============================================
# 3. TRAIN/VAL/TEST SPLIT (STRATIFIED)
# ============================================

print("\n" + "=" * 70)
print("3. TRAIN/VAL/TEST SPLIT (STRATIFIED)")
print("=" * 70)

from sklearn.model_selection import train_test_split

# Stratified split (giữ tỷ lệ label như nhau)
X = df_clean[feature_cols]
y = df_clean[target_col]

# Split 70/15/15 (stratified)
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, stratify=y, random_state=42
)

X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.176, stratify=y_temp, random_state=42  # 0.176*0.85 ≈ 0.15
)

# Map lại index để lấy metadata
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
print("4. TRAINING MODEL (Random Forest)")
print("=" * 70)

# Model 1: Random Forest (baseline)
model_rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42,
    class_weight='balanced',  # Cân bằng class (quan trọng nếu label không đều)
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
# Model 3: XGBoost (mạnh nhất)
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder

# Encode labels thành số
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_val_encoded = label_encoder.transform(y_val)
y_test_encoded = label_encoder.transform(y_test)

# Mapping: DOWN=0, NEUTRAL=1, UP=2 (alphabetical order)
print(f"Label mapping: {dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))}")

model_xgb = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='mlogloss',
    use_label_encoder=False  # Tắt warning
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
# XGBoost (predict → decode)
y_val_pred_xgb_encoded = model_xgb.predict(X_val)  # ← Predict ra số (0, 1, 2)
y_val_pred_xgb = label_encoder.inverse_transform(y_val_pred_xgb_encoded)  # ← Decode về string
acc_val_xgb = accuracy_score(y_val, y_val_pred_xgb)
print(f"\nXGBoost - Validation Accuracy: {acc_val_xgb:.4f}")
print(classification_report(y_val, y_val_pred_xgb, zero_division=0))

# Chọn model tốt nhất trong 3 models
best_acc = max(acc_val_rf, acc_val_gb, acc_val_xgb)

if best_acc == acc_val_xgb:
    best_model = model_xgb
    best_model_name = "XGBoost"
    print(f"\n✅ Selected model: {best_model_name} (acc: {acc_val_xgb:.4f})")
elif best_acc == acc_val_rf:
    best_model = model_rf
    best_model_name = "Random Forest"
    print(f"\n✅ Selected model: {best_model_name} (acc: {acc_val_rf:.4f})")
else:
    best_model = model_gb
    best_model_name = "Gradient Boosting"
    print(f"\n✅ Selected model: {best_model_name} (acc: {acc_val_gb:.4f})")
# ============================================
# 6. EVALUATE ON TEST SET (FINAL)
# ============================================

print("\n" + "=" * 70)
print("6. TEST SET PERFORMANCE (FINAL EVALUATION)")
print("=" * 70)

# Nếu model là XGBoost, cần decode
if best_model_name == "XGBoost":
    y_test_pred_encoded = best_model.predict(X_test)
    y_test_pred = label_encoder.inverse_transform(y_test_pred_encoded)
    y_test_proba = best_model.predict_proba(X_test)
else:
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
axes[0, 0].set_title(f'Confusion Matrix (Test Set)\nAccuracy: {acc_test:.2%}')
axes[0, 0].set_ylabel('Actual')
axes[0, 0].set_xlabel('Predicted')

# Plot 2: Feature Importance
axes[0, 1].barh(feature_importance['feature'], feature_importance['importance'])
axes[0, 1].set_xlabel('Importance')
axes[0, 1].set_title('Feature Importance')
axes[0, 1].invert_yaxis()
axes[0, 1].grid(alpha=0.3)

# Plot 3: Prediction distribution
test_label_dist = pd.Series(y_test_pred).value_counts()
axes[1, 0].bar(test_label_dist.index, test_label_dist.values, alpha=0.7, edgecolor='black')
axes[1, 0].set_xlabel('Predicted Label')
axes[1, 0].set_ylabel('Count')
axes[1, 0].set_title('Prediction Distribution (Test Set)')
axes[1, 0].grid(alpha=0.3)

# Plot 4: Accuracy by confidence (high confidence predictions)
test_df_eval = test_df.copy()
test_df_eval['predicted'] = y_test_pred
test_df_eval['confidence'] = y_test_proba.max(axis=1)
test_df_eval['correct'] = (test_df_eval['predicted'] == test_df_eval[target_col])

# Bin by confidence
bins = [0, 0.4, 0.6, 0.8, 1.0]
test_df_eval['conf_bin'] = pd.cut(test_df_eval['confidence'], bins=bins)
conf_acc = test_df_eval.groupby('conf_bin')['correct'].mean()

axes[1, 1].bar(range(len(conf_acc)), conf_acc.values, alpha=0.7, edgecolor='black')
axes[1, 1].set_xticks(range(len(conf_acc)))
axes[1, 1].set_xticklabels([str(b) for b in conf_acc.index], rotation=45)
axes[1, 1].set_ylabel('Accuracy')
axes[1, 1].set_xlabel('Confidence Range')
axes[1, 1].set_title('Accuracy by Model Confidence')
axes[1, 1].grid(alpha=0.3)
axes[1, 1].axhline(acc_test, color='red', linestyle='--', label=f'Overall: {acc_test:.2%}')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('model_evaluation_24h.png', dpi=300, bbox_inches='tight')
print("✓ Saved: model_evaluation_24h.png")

plt.show()

# ============================================
# 9. SAVE MODEL
# ============================================

print("\n" + "=" * 70)
print("9. SAVING MODEL...")
print("=" * 70)

model_filename = f'model_24h_{best_model_name.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d")}.pkl'
joblib.dump(best_model, model_filename)
print(f"✓ Model saved: {model_filename}")

# Save feature names (cần cho prediction sau này)
feature_info = {
    'feature_cols': feature_cols,
    'model_name': best_model_name,
    'test_accuracy': acc_test,
    'trained_date': datetime.now().isoformat(),
    'threshold': 0.2,  
    'horizon': '24h'  
}

import json
with open('model_info_24h.json', 'w') as f:
    json.dump(feature_info, f, indent=2)
print("✓ Model info saved: model_info_24h.json")

# ============================================
# 10. SAMPLE PREDICTIONS
# ============================================

print("\n" + "=" * 70)
print("10. SAMPLE PREDICTIONS (First 10 test samples)")
print("=" * 70)

test_sample = test_df.head(10).copy()
test_sample['predicted'] = best_model.predict(test_sample[feature_cols])
test_sample['confidence'] = best_model.predict_proba(test_sample[feature_cols]).max(axis=1)

display_cols = ['news_timestamp', 'symbol', 'sentiment_label', 'abret_24h', 'label', 'predicted', 'confidence']
print(test_sample[display_cols].to_string(index=False))

# ============================================
# 11. SUMMARY REPORT
# ============================================

print("\n" + "=" * 70)
print("📊 MODEL TRAINING SUMMARY")
print("=" * 70)

# Calculate per-class metrics
precision, recall, f1, support = precision_recall_fscore_support(y_test, y_test_pred, average=None, labels=['DOWN', 'NEUTRAL', 'UP'], zero_division=0)

print(f"""
MODEL DETAILS:
--------------
Model: {best_model_name}
Features: {len(feature_cols)} ({', '.join(feature_cols[:3])}...)
Training samples: {len(train_df)}
Test samples: {len(test_df)}

TEST SET PERFORMANCE:
---------------------
Overall Accuracy: {acc_test:.2%}

Per-class metrics:
  DOWN:
    - Precision: {precision[0]:.2%}
    - Recall: {recall[0]:.2%}
    - F1-Score: {f1[0]:.2%}
    - Support: {support[0]}
  
  NEUTRAL:
    - Precision: {precision[1]:.2%}
    - Recall: {recall[1]:.2%}
    - F1-Score: {f1[1]:.2%}
    - Support: {support[1]}
  
  UP:
    - Precision: {precision[2]:.2%}
    - Recall: {recall[2]:.2%}
    - F1-Score: {f1[2]:.2%}
    - Support: {support[2]}

TOP 3 IMPORTANT FEATURES:
-------------------------
1. {feature_importance.iloc[0]['feature']}: {feature_importance.iloc[0]['importance']:.4f}
2. {feature_importance.iloc[1]['feature']}: {feature_importance.iloc[1]['importance']:.4f}
3. {feature_importance.iloc[2]['feature']}: {feature_importance.iloc[2]['importance']:.4f}

MODEL SAVED:
------------
File: {model_filename}

CONCLUSION:
-----------
""")

if acc_test >= 0.70:
    print("✅ Model đạt accuracy ≥70% → TỐT, có thể deploy lên UI.")
elif acc_test >= 0.60:
    print("⚠️ Model đạt accuracy 60-70% → CHẤP NHẬN ĐƯỢC, nhưng cần cải thiện.")
else:
    print("❌ Model accuracy <60% → CẦN TUNE thêm (thêm features, thử model khác, hoặc thêm dữ liệu).")

print("\nNext steps:")
print("1. ✅ Chạy event_study_analysis.py (nếu chưa)")
print("2. ✅ Chạy train_model.py (bước này)")
print("3. ⏭️  Tạo explanation AI (giải thích 'lý do vì sao')")
print("4. ⏭️  Deploy model lên API (để UI gọi)")

print("=" * 70)