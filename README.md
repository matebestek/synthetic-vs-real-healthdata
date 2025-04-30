# synthetic-vs-real-healthdata
# Synthetic vs Real Data Quality Evaluation Toolkit

This repository contains a comprehensive Python-based analysis pipeline to evaluate the quality and utility of synthetic datasets against real datasets. It supports statistical similarity testing, distributional alignment, machine learning generalization, and regression-based assessments—especially tailored for health-related survey data.

## 📁 Project Structure

- `analysis_outputs.xlsx`: Contains formal test results (KS, Chi², DCR, AUROC, MMD, TSTR).
- `analysis_comparison_outputs.xlsx`: Contains regression, t-test, ANOVA, chi² and correlation analyses.
- `plots/`: Contains all generated visualizations (histograms, PCA, t-SNE, ROC, barplots, heatmaps).

## 📦 Dependencies

The code requires the following Python libraries:

```bash
pandas numpy matplotlib seaborn scikit-learn statsmodels scipy openpyxl
```

## 🚀 How to Use

1. Run the script in a Python environment with GUI access (for Excel file selection).
2. Select an Excel file with **Sheet 0 = Real Data**, **Sheet 1 = Synthetic Data**.
3. All results will be saved into Excel and plot folders.

## 📊 Analyses Performed

### 1. Descriptive Statistics

- Compares means and standard deviations of continuous variables.
- Compares frequency distributions of categorical variables.
- Results saved to `Continuous_Comparison` and `Categorical_Frequencies` sheets.

### 2. Distributional Similarity

- Overlay histograms and KDE plots (per variable)
- 12 combined histograms grid: `plots/All_Histograms_Grid.png`
- Formal tests:
  - Kolmogorov–Smirnov test (continuous)
  - Chi-square test (categorical)
  - Table: `Test_Results`

### 3. Correlation Structure

- Absolute differences of Pearson correlations.
- Heatmap: `plots/Corr_Diff_Heatmap.png`
- Combined matrix (real/synthetic/difference): `Combined_Correlations` sheet

### 4. Distance-Based Similarity Metrics

- **Wasserstein Distance**: Computed per variable, Table: `Wasserstein_Distance`
- **Maximum Mean Discrepancy (MMD)**: Single global score, Table: `MMD_Result`
- **Distance to Center of Real (DCR)**:
  - Histogram plot: `plots/DCR_histogram.png`
  - Stats summary: `DCR_Results` sheet

### 5. Dimensionality Reduction Visualization

- **PCA**: `plots/PCA_real_vs_synthetic.png`
- **t-SNE**: `plots/tSNE_real_vs_synthetic.png`

### 6. Real vs Synthetic Classification

- SVM classifier trained on real+synthetic.
- ROC curve: `plots/ROC_real_vs_synthetic.png`
- AUROC value: `AUROC_Result` sheet

### 7. TSTR Evaluation

- Random forest trained on synthetic, tested on real.
- For: `ExerciseHabit`, `ObesityGroup`, `IPAQcategoricScore`
- Barplot: `plots/TSTR_barplot.png`
- Accuracy table: `TSTR_Results` sheet

---

## 🧪 Extended Analyses (for Applied Research)

### Group Comparisons

- **t-Test**: Gender, ChronicDisease, ExerciseHabit groups → `tTest_Results`
- **ANOVA**: IPAQcategoricScore, ObesityGroup → `ANOVA_Results`

### Chi-Square Association

- Extended contingency tables → `Chi2_Results`

### Correlation Analysis

- Pearson correlation for key variable pairs → `Correlation_Results`

### Regression Models

- M1–M6: Linear models
- M7–M8: Multinomial logistic
- Output: `Regression_Results`

---

## 📄 Licensing & Citation

You are welcome to reuse and adapt this pipeline with citation. Please cite the repository and acknowledge the analysis structure in your work.

---

## 👤 Author

Developed by [Your Name], 2025  
For academic use in synthetic data evaluation and physical activity research.

