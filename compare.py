# 📦 Importlar
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from tkinter import filedialog
import scipy.stats as stats
import statsmodels.formula.api as smf
from scipy.stats import pearsonr, ttest_ind, f_oneway, ks_2samp, chi2_contingency, wasserstein_distance
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from scipy.spatial.distance import cdist
import statsmodels.api as sm
from statsmodels.formula.api import ols
from sklearn.metrics.pairwise import rbf_kernel
from openpyxl import Workbook
from sklearn.linear_model import LogisticRegression

# 📋 Genel Sabitler
SEED = 42  # Rastgelelik kontrolü için seed
output_path = "analysis_outputs.xlsx"
output_dir = "plots"

# 📂 Excel dosyası seç
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files", "*.xlsx *.xls")])

# 📥 Veriyi oku
df_real = pd.read_excel(file_path, sheet_name=0)
df_synth = pd.read_excel(file_path, sheet_name=1)

# 📋 Değişkenler
demographic_vars = ["Gender", "ExerciseHabit", "ChronicDisease"]

continuous_vars = [
    "Age", "BodyHeight", "BodyWeight", "HowManyYears", "PACEStotalscore",
    "BREQ2IntrinsicRegulation", "BREQ2IntrojectedRegulation",
    "BREQ2ExternalRegulation", "BREQ2Amotivation",
    "IPAQ_totalScore", "BodyMassIndex"
]

categorical_vars = ["IPAQcategoricScore", "ObesityGroup"]

# 🔗 Doğru kategorik kolonlar
categorical_columns = demographic_vars + categorical_vars

# 📂 Sonuç klasörleri
os.makedirs("plots", exist_ok=True)
os.makedirs("histograms", exist_ok=True)

# 📑 Tanımlayıcı İstatistikler
def continuous_summary(df, group_name):
    desc = df[continuous_vars].agg(['mean', 'std']).T
    desc.columns = [f"{group_name}_Mean", f"{group_name}_Std"]
    return desc

real_cont = continuous_summary(df_real, "Real")
synth_cont = continuous_summary(df_synth, "Synth")
combined_cont = real_cont.join(synth_cont)

# 📊 Kategorik Değişkenler Birleşik Frekans Tablosu
categorical_frequencies = []
for var in demographic_vars + categorical_vars:
    real_freq = df_real[var].value_counts(normalize=True).rename("Real_Frequency").reset_index()
    real_freq.columns = ["Category", "Real_Frequency"]
    synth_freq = df_synth[var].value_counts(normalize=True).rename("Synth_Frequency").reset_index()
    synth_freq.columns = ["Category", "Synth_Frequency"]
    merged = pd.merge(real_freq, synth_freq, on="Category", how="outer")
    merged["Variable"] = var
    categorical_frequencies.append(merged)

combined_categorical_frequencies = pd.concat(categorical_frequencies, ignore_index=True)
combined_categorical_frequencies = combined_categorical_frequencies[["Variable", "Category", "Real_Frequency", "Synth_Frequency"]]

# 🔗 Korelasyon Matrisi
real_corr = df_real[continuous_vars].corr()
synth_corr = df_synth[continuous_vars].corr()
corr_diff = (real_corr - synth_corr).abs()

# 🧮 Regresyon ve Grup Karşılaştırmaları
# (Eklenebilir: basit ve çoklu regresyon, t-test ve ANOVA sonuçları)

# 📊 Histogramlar
for var in continuous_vars:
    plt.figure(figsize=(10,5))
    sns.histplot(df_real[var], color='blue', label='Real', kde=True, stat='density', bins=20, alpha=0.5)
    sns.histplot(df_synth[var], color='orange', label='Synthetic', kde=True, stat='density', bins=20, alpha=0.5)
    plt.title(f"Distribution of {var}")
    plt.xlabel(var)
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"plots/{var}_comparison_hist.png")
    plt.close()

# 📈 Kalite Testleri
def statistical_similarity_tests(df_real, df_synth, categorical_columns):
    ks_results, chi2_results = [], []
    for col in df_real.columns:
        if col in df_synth.columns:
            if col in categorical_columns:
                real_counts = df_real[col].value_counts()
                synth_counts = df_synth[col].value_counts()
                combined = pd.concat([real_counts, synth_counts], axis=1).fillna(0)
                chi2_stat, p_value, _, _ = chi2_contingency(combined)
                chi2_results.append([col, chi2_stat, p_value])
            else:
                stat, p_value = ks_2samp(df_real[col].dropna(), df_synth[col].dropna())
                ks_results.append([col, stat, p_value])
    return ks_results, chi2_results

# 📋 Kalite Testlerini Hesapla
ks_results, chi2_results = statistical_similarity_tests(df_real, df_synth, categorical_columns)
ks_df = pd.DataFrame(ks_results, columns=["Variable", "KS_stat", "p_value"])
chi2_df = pd.DataFrame(chi2_results, columns=["Variable", "Chi2_stat", "p_value"])
ks_df["Test"] = "KS"
chi2_df["Test"] = "Chi²"
ks_df["Pass"] = ks_df["p_value"] > 0.05
chi2_df["Pass"] = chi2_df["p_value"] > 0.05
quality_results_df = pd.concat([ks_df, chi2_df], ignore_index=True)
quality_results_df["Statistic"] = quality_results_df["KS_stat"].combine_first(quality_results_df["Chi2_stat"])
quality_results_df = quality_results_df[["Test", "Variable", "Statistic", "p_value", "Pass"]]

# 📋 Numerical Kolonları Belirle
numerical_cols = df_real.select_dtypes(include='number').columns.intersection(df_synth.columns)
# 📏 Sentetik veri için DCR hesaplama
scaler = StandardScaler()
real_scaled = scaler.fit_transform(df_real[numerical_cols])
synth_scaled = scaler.transform(df_synth[numerical_cols])

center_real = real_scaled.mean(axis=0)
distances_synth = cdist(synth_scaled, [center_real], metric='euclidean').flatten()

# 📏 Gerçek veri içi DCR (Train vs Test)
train_real, test_real = train_test_split(df_real[numerical_cols], test_size=0.3, random_state=SEED)

scaler_real = StandardScaler()
train_real_scaled = scaler_real.fit_transform(train_real)
test_real_scaled = scaler_real.transform(test_real)

center_train_real = train_real_scaled.mean(axis=0)
distances_real = cdist(test_real_scaled, [center_train_real], metric='euclidean').flatten()

# 📑 Sonuçları Tek Bir DataFrame'e Topla
dcr_metrics = {
    "Measure": [
        "Synthetic Mean Distance", "Synthetic Median Distance", "Synthetic Min Distance", "Synthetic Max Distance",
        "Real Mean Distance", "Real Median Distance", "Real Min Distance", "Real Max Distance"
    ],
    "Value": [
        np.mean(distances_synth),
        np.median(distances_synth),
        np.min(distances_synth),
        np.max(distances_synth),
        np.mean(distances_real),
        np.median(distances_real),
        np.min(distances_real),
        np.max(distances_real)
    ]
}

dcr_combined_df = pd.DataFrame(dcr_metrics)

# 📈 PCA ve t-SNE
combined_data = pd.concat([df_real[numerical_cols].assign(Source="Real"), df_synth[numerical_cols].assign(Source="Synthetic")], ignore_index=True)
X = combined_data.drop("Source", axis=1)
y = combined_data["Source"]
X_scaled = StandardScaler().fit_transform(X)

pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2"])
pca_df["Source"] = y.values

plt.figure(figsize=(8,6))
sns.scatterplot(data=pca_df, x="PC1", y="PC2", hue="Source", alpha=0.6)
plt.title("PCA: Real vs Synthetic")
plt.tight_layout()
plt.savefig("plots/PCA_real_vs_synthetic.png")
plt.close()

tsne = TSNE(n_components=2, perplexity=30, random_state=42)
X_tsne = tsne.fit_transform(X_scaled)
tsne_df = pd.DataFrame(X_tsne, columns=["Dim1", "Dim2"])
tsne_df["Source"] = y.values

plt.figure(figsize=(8,6))
sns.scatterplot(data=tsne_df, x="Dim1", y="Dim2", hue="Source", alpha=0.6)
plt.title("t-SNE: Real vs Synthetic")
plt.tight_layout()
plt.savefig("plots/tSNE_real_vs_synthetic.png")
plt.close()

# 📈 Corr Diff için Basit Heatmap (sadece farklar)
plt.figure(figsize=(10,8))
sns.heatmap(corr_diff, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={'label': 'Absolute Correlation Difference'})
plt.title("Correlation Difference Heatmap (Real vs Synthetic)")
plt.tight_layout()
plt.savefig("plots/Corr_Diff_Heatmap.png", dpi=300)
plt.close()

# 📈 Real, Synthetic ve Difference bir arada gösterilen gelişmiş Heatmap
annot_data = real_corr.copy()
for i in annot_data.index:
    for j in annot_data.columns:
        real_val = real_corr.loc[i, j]
        synth_val = synth_corr.loc[i, j]
        diff_val = corr_diff.loc[i, j]
        annot_data.loc[i, j] = f"{real_val:.2f}\n{synth_val:.2f}\n{diff_val:.2f}"

# 📈 Corr Diff için Heatmap (sadece farklar gösterilecek)
plt.figure(figsize=(10,8))
sns.heatmap(corr_diff, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={'label': 'Absolute Correlation Difference'})
plt.title("Correlation Difference Heatmap (Real vs Synthetic)")
plt.tight_layout()
plt.savefig("plots/Corr_Diff_Heatmap.png", dpi=300)
plt.close()


# 🎯 Real, Synthetic ve Difference değerlerini birleştir
combined_corr = real_corr.copy()
for i in combined_corr.index:
    for j in combined_corr.columns:
        real_val = real_corr.loc[i, j]
        synth_val = synth_corr.loc[i, j]
        diff_val = corr_diff.loc[i, j]
        combined_corr.loc[i, j] = f"{real_val:.2f}\n{synth_val:.2f}\n{diff_val:.2f}"




# 📏 Wasserstein Distance
wasserstein_results = []
for var in continuous_vars:
    wd = wasserstein_distance(df_real[var].dropna(), df_synth[var].dropna())
    wasserstein_results.append((var, wd))
wasserstein_df = pd.DataFrame(wasserstein_results, columns=["Variable", "Wasserstein_Distance"])

# 📈 AUROC Hesaplama
X_combined = pd.concat([df_real[continuous_vars], df_synth[continuous_vars]], ignore_index=True)
y_combined = np.array([0]*len(df_real) + [1]*len(df_synth))
scaler_roc = StandardScaler()
X_scaled = scaler_roc.fit_transform(X_combined)

clf = SVC(kernel='linear', probability=True, random_state=42)
clf.fit(X_scaled, y_combined)
probs = clf.predict_proba(X_scaled)[:,1]
fpr, tpr, thresholds = roc_curve(y_combined, probs)
auc_score = roc_auc_score(y_combined, probs)

plt.figure(figsize=(8,6))
plt.plot(fpr, tpr, label=f'AUC = {auc_score:.3f}')
plt.plot([0,1], [0,1], linestyle='--', color='gray')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve: Real vs Synthetic')
plt.legend()
plt.tight_layout()
plt.savefig("plots/ROC_real_vs_synthetic.png", dpi=300)
plt.close()

auroc_df = pd.DataFrame({"Measure": ["AUROC"], "Value": [auc_score]})

# 📏 MMD Hesaplama
scaler_mmd = StandardScaler()
real_scaled = scaler_mmd.fit_transform(df_real[continuous_vars])
synth_scaled = scaler_mmd.transform(df_synth[continuous_vars])

def compute_mmd(X, Y, gamma=1.0):
    XX = rbf_kernel(X, X, gamma=gamma)
    YY = rbf_kernel(Y, Y, gamma=gamma)
    XY = rbf_kernel(X, Y, gamma=gamma)
    return XX.mean() + YY.mean() - 2 * XY.mean()

mmd_score = compute_mmd(real_scaled, synth_scaled, gamma=1.0)
mmd_df = pd.DataFrame({"Measure": ["MMD"], "Value": [mmd_score]})





print("\n✅ Full Analysis and Advanced Quality Tests Completed! All results saved to 'analysis_outputs.xlsx' and 'plots/' folder.")
# 📈 TSTR Testleri ve Barplot
def run_tstr(real_df, synthetic_df, target_col, categorical_columns=[]):
    common_cols = real_df.columns.intersection(synthetic_df.columns)
    X_synth = synthetic_df[common_cols].drop(columns=[target_col])
    y_synth = synthetic_df[target_col]
    X_real = real_df[common_cols].drop(columns=[target_col])
    y_real = real_df[target_col]

    # Categorical olanları kategorik yap
    for col in categorical_columns:
        if col in X_synth.columns:
            X_synth[col] = X_synth[col].astype("category")
            X_real[col] = X_real[col].astype("category")

    # Scale sadece sayısal kolonlara
    scaler = StandardScaler()
    X_synth_scaled = scaler.fit_transform(X_synth.select_dtypes(include='number'))
    X_real_scaled = scaler.transform(X_real.select_dtypes(include='number'))

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_synth_scaled, y_synth)
    y_pred = clf.predict(X_real_scaled)

    acc = accuracy_score(y_real, y_pred)

    summary = pd.DataFrame({
        "Target": [target_col],
        "TSTR Accuracy": [acc]
    })

    return summary

# TSTR Hedef değişkenler
tstr_summaries = []
tstr_summaries.append(run_tstr(df_real, df_synth, target_col="ExerciseHabit", categorical_columns=categorical_vars))
tstr_summaries.append(run_tstr(df_real, df_synth, target_col="ObesityGroup", categorical_columns=categorical_vars))
tstr_summaries.append(run_tstr(df_real, df_synth, target_col="IPAQcategoricScore", categorical_columns=categorical_vars))

tstr_df = pd.concat(tstr_summaries, ignore_index=True)

# 📈 TSTR Barplot
plt.figure(figsize=(10,6))
sns.barplot(data=tstr_df, x="Target", y="TSTR Accuracy", palette="Blues_d")
plt.ylim(0,1)
plt.title("TSTR Accuracy by Target Variable")
plt.ylabel("Accuracy")
plt.xlabel("Target Variable")
plt.tight_layout()
plt.savefig("plots/TSTR_barplot.png", dpi=300)
plt.close()

# 📊 DCR Histogramı (Sentetik Veri)
plt.figure(figsize=(8, 4))
plt.hist(distances_synth, bins=30, color="skyblue", edgecolor="black")
plt.title("Distance to Center of Real (DCR) - Synthetic Data")
plt.xlabel("Euclidean Distance")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{output_dir}/DCR_histogram.png", dpi=300)
plt.close()

print("✅ DCR Histogramı kaydedildi (plots/DCR_histogram.png).")


print("\n✅ TSTR Barplot and DCR Histogram created and saved to 'plots/' folder!")

# 📂 Sonuçları kaydetmek için Excel
output_path = "analysis_comparison_outputs.xlsx"



# 📋 Model Listeleri
models = [
    {"target": "IPAQ_totalScore", "predictors": ["BREQ2IntrinsicRegulation", "BREQ2IntrojectedRegulation", "BREQ2ExternalRegulation", "BREQ2Amotivation", "Age", "BodyMassIndex", "Gender"], "type": "linear"},
    {"target": "PACEStotalscore", "predictors": ["Age", "BodyMassIndex", "Gender", "IPAQ_totalScore"], "type": "linear"},
    {"target": "BodyMassIndex", "predictors": ["Age", "Gender", "ChronicDisease", "ExerciseHabit"], "type": "linear"},
    {"target": "IPAQcategoricScore", "predictors": ["Age", "BodyMassIndex", "BREQ2IntrinsicRegulation", "BREQ2IntrojectedRegulation", "BREQ2ExternalRegulation", "BREQ2Amotivation"], "type": "logistic"}
]
# 📋 Fonksiyonlar
def run_linear_regression(df, target, predictors):
    formula = target + ' ~ ' + ' + '.join(predictors)
    model = smf.ols(formula=formula, data=df).fit()
    return model.rsquared, model.rsquared_adj, model.fvalue, model.f_pvalue

def run_multinomial_logistic(df, target, predictors):
    X = df[predictors]
    y = df[target]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=500, random_state=42)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    acc = accuracy_score(y, y_pred)
    return acc


def t_test_analysis(df1, df2, group_cols, targets):
    records = []
    for group_col in group_cols:
        for target in targets:
            for name, df in zip(["Real", "Synthetic"], [df1, df2]):
                if df[group_col].nunique() == 2:
                    levels = df[group_col].dropna().unique()
                    group1 = df[df[group_col]==levels[0]][target].dropna()
                    group2 = df[df[group_col]==levels[1]][target].dropna()
                    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=True)
                    records.append({
                        "Group": group_col,
                        "Target": target,
                        "Dataset": name,
                        "Test": "t-test",
                        "Statistic": t_stat,
                        "p-value": p_val,
                        "Group1 Mean": group1.mean(),
                        "Group2 Mean": group2.mean()
                    })
    return pd.DataFrame(records)

def anova_analysis(df1, df2, group_cols, targets):
    records = []
    for group_col in group_cols:
        for target in targets:
            for name, df in zip(["Real", "Synthetic"], [df1, df2]):
                if df[group_col].nunique() > 2:
                    groups = [g[target].dropna() for _, g in df.groupby(group_col)]
                    f_stat, p_val = stats.f_oneway(*groups)
                    records.append({
                        "Group": group_col,
                        "Target": target,
                        "Dataset": name,
                        "Test": "ANOVA",
                        "Statistic": f_stat,
                        "p-value": p_val
                    })
    return pd.DataFrame(records)
def chi2_test_analysis(df1, df2, var1, var2):
    records = []
    for name, df in zip(["Real", "Synthetic"], [df1, df2]):
        contingency = pd.crosstab(df[var1], df[var2])
        chi2, p, dof, _ = stats.chi2_contingency(contingency)
        records.append({
            "Analysis": f"{var1} vs {var2}",
            "Dataset": name,
            "Chi2": chi2,
            "p-value": p,
            "Degrees of Freedom": dof
        })
    return pd.DataFrame(records)

def correlation_analysis(df1, df2, col1, col2):
    records = []
    for name, df in zip(["Real", "Synthetic"], [df1, df2]):
        corr, p = stats.pearsonr(df[col1].dropna(), df[col2].dropna())
        records.append({
            "Analysis": f"{col1} ↔ {col2}",
            "Dataset": name,
            "Pearson r": corr,
            "p-value": p
        })
    return pd.DataFrame(records)

# 🔢 Extended Chi-Square ve Korelasyon Analizleri
chi_square_pairs = [
    ("Gender", "ExerciseHabit"),
    ("Gender", "ChronicDisease"),
    ("Gender", "ObesityGroup"),
    ("ExerciseHabit", "ChronicDisease"),
    ("ExerciseHabit", "ObesityGroup"),
    ("ChronicDisease", "ObesityGroup"),
    ("IPAQcategoricScore", "ObesityGroup"),
    ("ExerciseHabit", "IPAQcategoricScore")
]

correlation_pairs = [
    ("Age", "BodyMassIndex"),
    ("Age", "IPAQ_totalScore"),
    ("PACEStotalscore", "IPAQ_totalScore"),
    ("BREQ2IntrinsicRegulation", "IPAQ_totalScore"),
    ("BREQ2IntrojectedRegulation", "IPAQ_totalScore"),
    ("BREQ2ExternalRegulation", "IPAQ_totalScore"),
    ("BREQ2Amotivation", "IPAQ_totalScore"),
    ("BodyMassIndex", "IPAQ_totalScore"),
    ("BodyMassIndex", "PACEStotalscore")
]

extended_chi2_records = []
for var1, var2 in chi_square_pairs:
    extended_chi2_records.append(chi2_test_analysis(df_real, df_synth, var1, var2))

extended_corr_records = []
for var1, var2 in correlation_pairs:
    extended_corr_records.append(correlation_analysis(df_real, df_synth, var1, var2))

extended_chi2_df = pd.concat(extended_chi2_records, ignore_index=True)
extended_corr_df = pd.concat(extended_corr_records, ignore_index=True)

def regression_analysis(df1, df2, target, predictors):
    records = []
    formula = target + " ~ " + " + ".join(predictors)
    for name, df in zip(["Real", "Synthetic"], [df1, df2]):
        model = smf.ols(formula=formula, data=df).fit()
        records.append({
            "Analysis": f"{target} ~ {', '.join(predictors)}",
            "Dataset": name,
            "R-squared": model.rsquared,
            "Adj. R-squared": model.rsquared_adj,
            "F-statistic": model.fvalue,
            "F p-value": model.f_pvalue
        })
    return pd.DataFrame(records)
# 📊 Tüm Sonuçları Toplama
regression_records = []
for model_info in models:
    target = model_info["target"]
    predictors = model_info["predictors"]
    model_type = model_info["type"]
    for dataset_name, df in zip(["Real", "Synthetic"], [df_real, df_synth]):
        if model_type == "linear":
            formula = target + ' ~ ' + ' + '.join(predictors)
            model = smf.ols(formula=formula, data=df).fit()
            regression_records.append({
                "Model": f"{target} ~ {' + '.join(predictors)}",
                "Dataset": dataset_name,
                "R-squared": model.rsquared,
                "Adj. R-squared": model.rsquared_adj,
                "F-statistic": model.fvalue,
                "F p-value": model.f_pvalue
            })
        elif model_type == "logistic":
            X = df[predictors]
            y = df[target]
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            clf = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=500, random_state=42)
            clf.fit(X_scaled, y)
            y_pred = clf.predict(X_scaled)
            acc = accuracy_score(y, y_pred)
            regression_records.append({
                "Model": f"{target} ~ {' + '.join(predictors)}",
                "Dataset": dataset_name,
                "Accuracy": acc
            })

regression_results_df = pd.DataFrame(regression_records)

# 📊 Analizler
t_targets = ["IPAQ_totalScore", "PACEStotalscore"]

# t-Test
ttest_df = t_test_analysis(df_real, df_synth, group_cols=["ExerciseHabit", "Gender", "ChronicDisease"], targets=t_targets)

# ANOVA
anova_df = anova_analysis(df_real, df_synth, group_cols=["IPAQcategoricScore", "ObesityGroup"], targets=t_targets)

# Chi2-Test (ilk)
chi2_df = chi2_test_analysis(df_real, df_synth, var1="Gender", var2="IPAQcategoricScore")

# Korelasyon (ilk)
corr_df = correlation_analysis(df_real, df_synth, col1="HowManyYears", col2="PACEStotalscore")


# Extended Chi2 ve Korelasyon
extended_chi2_records = []
for var1, var2 in chi_square_pairs:
    extended_chi2_records.append(chi2_test_analysis(df_real, df_synth, var1, var2))

extended_corr_records = []
for var1, var2 in correlation_pairs:
    extended_corr_records.append(correlation_analysis(df_real, df_synth, var1, var2))

full_chi2_df = pd.concat([chi2_df, extended_chi2_df], ignore_index=True)
full_corr_df = pd.concat([corr_df, extended_corr_df], ignore_index=True)





# 📥 Sonuçları Excel'e Kaydet
with pd.ExcelWriter("analysis_outputs.xlsx", engine="openpyxl") as writer:
    combined_cont.to_excel(writer, sheet_name="Continuous_Comparison", index=True)
    combined_categorical_frequencies.to_excel(writer, sheet_name="Categorical_Frequencies", index=False)
    combined_corr.to_excel(writer, sheet_name="Combined_Correlations", index=True)
    quality_results_df.to_excel(writer, sheet_name="Test_Results", index=False)
    dcr_combined_df.to_excel(writer, sheet_name="DCR_Results", index=False)
    wasserstein_df.to_excel(writer, sheet_name="Wasserstein_Distance", index=False)
    auroc_df.to_excel(writer, sheet_name="AUROC_Result", index=False)
    mmd_df.to_excel(writer, sheet_name="MMD_Result", index=False)
    tstr_df.to_excel(writer, sheet_name="TSTR_Results", index=False)

with pd.ExcelWriter("analysis_comparison_outputs.xlsx", engine="openpyxl") as writer:
    ttest_df.to_excel(writer, sheet_name="tTest_Results", index=False)
    anova_df.to_excel(writer, sheet_name="ANOVA_Results", index=False)
    full_chi2_df.to_excel(writer, sheet_name="Chi2_Results", index=False)
    full_corr_df.to_excel(writer, sheet_name="Correlation_Results", index=False)
    regression_results_df.to_excel(writer, sheet_name="Regression_Results", index=False)


print("\n✅ Tüm analizler tamamlandı ve iki Excel dosyasına kaydedildi!")

fig, axes = plt.subplots(nrows=4, ncols=3, figsize=(18, 14))
axes = axes.flatten()

for idx, var in enumerate(continuous_vars):
    sns.histplot(df_real[var], color='blue', label='Real', kde=True, stat='density', bins=20, alpha=0.5, ax=axes[idx])
    sns.histplot(df_synth[var], color='orange', label='Synthetic', kde=True, stat='density', bins=20, alpha=0.5, ax=axes[idx])
    axes[idx].set_title(f"{var}")
    axes[idx].legend()

# Eğer 12 subplot varsa ve sonuncusu boş kalıyorsa onu sil
if len(continuous_vars) < len(axes):
    for j in range(len(continuous_vars), len(axes)):
        fig.delaxes(axes[j])

plt.tight_layout()
plt.suptitle("Overlay Histograms for Continuous Variables", fontsize=16, y=1.02)
plt.savefig("plots/All_Histograms_Grid.png", dpi=300)
plt.close()

