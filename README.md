# SpaceX Falcon 9 Landing Prediction

## Project Overview
This project analyzes historical SpaceX Falcon 9 launch data and uses machine learning to classify first-stage landing outcomes.

The project demonstrates an end-to-end data science workflow, including data collection, cleaning, exploratory data analysis, visualization, and machine learning model evaluation.

## Technologies Used
- Python
- Pandas and NumPy
- Matplotlib
- Scikit-learn
- Jupyter Notebook and Google Colab
- Git and GitHub

## Project Workflow
1. **Data Collection:** Collect launch data from available sources.
2. **Data Cleaning:** Prepare and label historical launch records.
3. **Exploratory Data Analysis:** Explore launch characteristics and landing outcomes.
4. **Machine Learning:** Train and compare four classification models.
5. **Model Evaluation:** Evaluate accuracy, precision, recall, F1-score, and confusion matrices.

## Machine Learning Results

| Model | Accuracy | F1-Score |
|---|---:|---:|
| Logistic Regression | 84.6% | 90.9% |
| Decision Tree | 88.5% | 93.3% |
| Random Forest | 88.5% | 93.3% |
| Support Vector Machine (RBF) | 84.6% | 91.3% |

Decision Tree and Random Forest achieved the highest accuracy of **88.5%** on the held-out test set.

## Dataset Limitations
The machine learning dataset contains 104 labeled records, including 91 successful and 13 unsuccessful landings. The dataset is small and imbalanced, so these results are educational and should not be interpreted as reliable predictions of future launches.

## Repository Structure
- `src/` — Python scripts for collection, cleaning, and analysis
- `data/processed/` — Cleaned and labeled datasets
- `notebooks/` — Exploratory analysis and machine learning notebooks
- `requirements.txt` — Project dependencies
- `Capstone Project.pptx` — Project presentation

## How to Run
1. Open the machine learning notebook from the `notebooks` folder in Google Colab.
2. Upload `falcon9_launches_labeled.csv` from `data/processed/` when prompted.
3. Run the notebook cells in order.
4. Review the model comparison table and confusion matrices.

## Conclusion
This project demonstrates practical Python programming, data preparation, exploratory analysis, and supervised machine learning evaluation using historical rocket launch data.

## Acknowledgment
Based on the SpaceX Falcon 9 landing prediction capstone topic from the IBM Data Science learning program, with a historical dataset and project-specific implementation.
