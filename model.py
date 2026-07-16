import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib
import matplotlib.pyplot as plt


df1 = pd.read_csv(r"C:\Users\User\Desktop\проекты\windguard_2.0\WindGuard_v3_2015_2019.csv")
df2 = pd.read_csv(r"C:\Users\User\Desktop\проекты\windguard_2.0\WindGuard_v3_2020_2025.csv")
df = pd.concat([df1, df2]).reset_index(drop=True)
df = df.dropna()
print(f"Датасет загружен: {df.shape}")

# !!! ПЕРЕНОСИМ НАВЕРХ !!!
target_scaler = MinMaxScaler()
df['erosion_risk'] = target_scaler.fit_transform(df[['erosion_risk']])
print("Целевая переменная нормализована от 0 до 1.")

# Теперь делаем сплит — и в train/test попадут уже нормализованные значения!
train = df[df['year'] <= 2022].copy()
test = df[df['year'] > 2022].copy()


# Простые признаки
for dataset in [train, test]:
    dataset["ndvi_wind_interaction"] = (
        dataset["NDVI_now"] * dataset["wind_max"]
    )
    dataset["wind_erosivity"] = (
        dataset["wind_max"] ** 3
    )
    dataset["aridity_index"] = (
        dataset["rain"] /
        (dataset["evaporation"].abs() + 1e-9)
    )
    dataset["is_dry_season"] = (
        dataset["month"].isin([3, 4, 5]).astype(int)
    )

# Статистика только по train
monthly_mean = train.groupby("month")["NDVI_now"].mean()
monthly_std = train.groupby("month")["NDVI_now"].std()

train["ndvi_zscore"] = (
    train["NDVI_now"]
    - train["month"].map(monthly_mean)
) / (
    train["month"].map(monthly_std) + 1e-9
)

test["ndvi_zscore"] = (
    test["NDVI_now"]
    - test["month"].map(monthly_mean)
) / (
    test["month"].map(monthly_std) + 1e-9
)

biome_mean = train.groupby(
    ["biome", "month"]
)["NDVI_now"].mean()

global_mean = train["NDVI_now"].mean()

train["ndvi_biome_anomaly"] = train.apply(
    lambda row: row["NDVI_now"]
    - biome_mean.loc[(row["biome"], row["month"])],
    axis=1
)

test["ndvi_biome_anomaly"] = test.apply(
    lambda row: row["NDVI_now"]
    - biome_mean.get(
        (row["biome"], row["month"]),
        global_mean
    ),
    axis=1
)

print("Фичи успешно созданы.")

features = [
    "NDVI_now", "wind_mean", "wind_max", "wind_erosivity", "rain", "tempC", 
    "soil_moisture", "evaporation", "slope", "soil_type", "biome", "month", 
    "latitude", "longitude", "ndvi_wind_interaction", "aridity_index", 
    "is_dry_season", "ndvi_zscore", "ndvi_biome_anomaly"
]


X_train = train[features]
X_test = test[features]

y_train = train["erosion_risk"]
y_test = test["erosion_risk"]


print(f"Train: {X_train.shape}")
print(f"Test: {X_test.shape}")


sample_weights = np.where(y_train > 0.7, 5.0, 1.0)


scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc = scaler.transform(X_test)


corr = train[features + ["erosion_risk"]].corr()["erosion_risk"]
print(corr.sort_values(ascending=False))

model = XGBRegressor(
    n_estimators=500,
    max_depth=5,
    learning_rate=0.03,
    subsample=0.7,
    colsample_bytree=0.9,
    min_child_weight=5,
    eval_metric="mae",
    random_state=42,
    n_jobs=-1
)

print("\nОбучаем модель...")
model.fit(X_train_sc, y_train, sample_weight=sample_weights)
print("Готово!")


preds = model.predict(X_test_sc)
print(preds.min(), preds.max())
print(y_test.min(), y_test.max())

print("\n=== Общие метрики ===")
print(f"MAE: {mean_absolute_error(y_test, preds):.4f}")
print(f"MSE: {mean_squared_error(y_test, preds):.4f}")
print(f"R²: {r2_score(y_test, preds):.4f}")

test = test.copy()

test["prediction"] = preds
test["error"] = abs(
    test["erosion_risk"] - test["prediction"]
)

plt.figure(figsize=(10, 8))

plt.scatter(
    test["longitude"],
    test["latitude"],
    c=test["error"],
    cmap="Reds",
    s=3
)

plt.colorbar(label="Absolute Error")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("WindGuard Model Error Map")

plt.show()

mask_high_risk = y_test > 0.7
mask_low_risk = y_test <= 0.7

print(f"\n=== На случаях высокого риска эрозии (risk > 0.7) ===")
print(f"Точек: {mask_high_risk.sum()}")
if mask_high_risk.sum() > 0:
    print(f"MAE: {mean_absolute_error(y_test[mask_high_risk], preds[mask_high_risk]):.4f}")
    print(f"R²: {r2_score(y_test[mask_high_risk], preds[mask_high_risk]):.4f}")

print(f"\n=== На случаях низкого/среднего риска (risk <= 0.7) ===")
print(f"Точек: {mask_low_risk.sum()}")
if mask_low_risk.sum() > 0:
    print(f"MAE: {mean_absolute_error(y_test[mask_low_risk], preds[mask_low_risk]):.4f}")
    print(f"R²: {r2_score(y_test[mask_low_risk], preds[mask_low_risk]):.4f}")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].scatter(y_test[:2000], preds[:2000], alpha=0.2, s=5)
axes[0].plot([0, 1], [0, 1], 'r--')  
axes[0].set_xlabel("Real")
axes[0].set_ylabel("Predicted")
axes[0].set_title("Real vs Predicted")

feat_imp = pd.Series(model.feature_importances_, index=features).sort_values()
feat_imp.plot(kind='barh', ax=axes[1])
axes[1].set_title("Importance")

residuals = y_test - preds
axes[2].hist(residuals, bins=50)
axes[2].set_xlabel("Error")
axes[2].set_title("Error distribution")

plt.tight_layout()
plt.savefig(r"C:\Users\User\Desktop\проекты\windguard_2.0\model_v3_results.png", dpi=150)
plt.show()

print("Пороги рисков по квантилям:")
print(f"Низкий риск (медиана): {np.percentile(preds, 50):.4f}")
print(f"Средний риск (75-й процентиль): {np.percentile(preds, 75):.4f}")
print(f"Высокий риск (90-й процентиль): {np.percentile(preds, 90):.4f}")
print(f"Критический риск (99-й процентиль): {np.percentile(preds, 99):.4f}")


ndvi_stats = df.groupby('month')['NDVI_now'].agg(['mean','std']).to_dict()
ndvi_biome_stats = df.groupby(['biome','month'])['NDVI_now'].mean().to_dict()

print("=== Проверка диапазонов ===")
print("y_train:", y_train.min(), y_train.max())
print("y_test :", y_test.min(), y_test.max())
print("preds  :", preds.min(), preds.max())

joblib.dump(ndvi_stats, r"C:\Users\User\Desktop\проекты\windguard_2.0\ndvi_stats.pkl")
joblib.dump(ndvi_biome_stats, r"C:\Users\User\Desktop\проекты\windguard_2.0\ndvi_biome_stats.pkl")
print("Статистика сохранена!")

joblib.dump(model, r"C:\Users\User\Desktop\проекты\windguard_2.0\xgb_model_v3.pkl")
joblib.dump(scaler, r"C:\Users\User\Desktop\проекты\windguard_2.0\scaler_v3.pkl")
joblib.dump(features, r"C:\Users\User\Desktop\проекты\windguard_2.0\features_v3.pkl")

print("\nГотово! Все файлы успешно сохранены для интеграции с FastAPI.")

import shap
import warnings
warnings.filterwarnings('ignore')

X_train_summary = shap.kmeans(X_train_sc, 5) 

explainer = shap.KernelExplainer(model.predict, X_train_summary)

X_test_sample_sc = X_test_sc[:50]

shap_values = explainer.shap_values(X_test_sample_sc)

plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test_sample_sc, feature_names=features, show=False)

plt.tight_layout()
plt.savefig(r"C:\Users\User\Desktop\проекты\windguard_2.0\shap_importance.png", dpi=150)
plt.show()

print("\nГрафик SHAP успешно построен и сохранен!")