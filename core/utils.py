import pandas as pd


def import_data():
    df = pd.read_excel('Kundendaten_Bearbeitungsdaten_200.xlsx')
    b_df = pd.read_excel('Kundendaten_Bearbeitungsdaten_200.xlsx', sheet_name='Bearbeitungsdaten')

    # Convert the date columns to pandas datetime format
    df['Datum Anfrage'] = pd.to_datetime(df['Datum Anfrage'], format="%d.%m.%Y")
    df['Datum Bestellung'] = pd.to_datetime(df['Datum Bestellung'], format="%d.%m.%Y")
    df['Datum Wiedervorlage'] = pd.to_datetime(df['Datum Wiedervorlage'], format="%d.%m.%Y")

    df.columns = df.columns.str.replace(' ', '_')
    df.columns = df.columns.str.replace("-", "_")
    df.columns = df.columns.str.replace(".", "")

    return df, b_df

def evaluate_customer(df):
  """
  Evaluates a customer based on their data in the DataFrame.

  Args:
      df: A Pandas DataFrame containing customer data.

  Returns:
      A float between 0 and 1 representing the customer's evaluation.
  """

  period = (df[2] - df[1]).days
  changes_before = df[4]
  changes_after = df[5]
  information_method = df[3]
  information_method_value = 0
  evaluation = 0

  weight_period = 0.5
  weight_changes_before = 0.1
  weight_changes_after = 0.2
  weight_information_method = 0.2

  # Factor in the information submission method.
  if information_method == 'Messe':
    information_method_value = 0.3
  elif information_method == 'Email':
    information_method_value = 0.2
  elif information_method == 'Website':
    information_method_value = 0.2
  # ... and so on for other methods.

  norm_period = min(period/30, 1)
  norm_changes_before = min(changes_before/5, 1)
  norm_changes_after = min(changes_after/5, 1)

  evaluation = (weight_period * (1 - norm_period) +
                weight_changes_before * (1 - norm_changes_before) +
                weight_changes_after * (1 - norm_changes_after) +
                weight_information_method * information_method_value)

  return evaluation


def get_data():
    df, b_df = import_data()
    df['Evaluation'] = df.apply(evaluate_customer, axis=1)

    print(list(df.columns))

    return df, b_df