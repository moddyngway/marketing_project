from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        df, b_df = get_data()

        # Filter data based on time filter
        time_filter = self.request.GET.get('time_filter')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')



        # Get default weights
        weight_period = 0.5
        weight_changes_before = 0.1
        weight_changes_after = 0.2
        weight_information_method = 0.2

        # Update evaluations with current weights
        df['Evaluation'] = df.apply(lambda row: evaluate_customer(row, weight_period, weight_changes_before, weight_changes_after, weight_information_method), axis=1)

        if time_filter:
            df = filter_data(df, time_filter)
        elif start_date and end_date:
            df = filter_custom_data(df, start_date, end_date)

        context['df'] = df.to_dict(orient='records')
        context['b_df'] = b_df.to_dict(orient='records')
        context['weight_period'] = weight_period
        context['weight_changes_before'] = weight_changes_before
        context['weight_changes_after'] = weight_changes_after
        context['weight_information_method'] = weight_information_method
        return context

    def post(self, request, *args, **kwargs):
        # Handle POST request
        weight_period = float(request.POST.get('weight_period', 0.5))
        weight_changes_before = float(request.POST.get('weight_changes_before', 0.1))
        weight_changes_after = float(request.POST.get('weight_changes_after', 0.2))
        weight_information_method = float(request.POST.get('weight_information_method', 0.2))

        context = self.get_context_data()

        df = pd.DataFrame(context['df'])
        df['Evaluation'] = df.apply(lambda row: evaluate_customer(row, weight_period, weight_changes_before, weight_changes_after, weight_information_method), axis=1)
        context['df'] = df.to_dict(orient='records')

        context['weight_period'] = weight_period
        context['weight_changes_before'] = weight_changes_before
        context['weight_changes_after'] = weight_changes_after
        context['weight_information_method'] = weight_information_method

        return self.render_to_response(context)


class BearbeitungsdatenView(View):
    template_name = 'core/bearbeitungsdaten.html'

    def get(self, request, *args, **kwargs):
        kunde_nr = kwargs.get('kunde_nr')
        _, b_df = get_data()
        bearbeitungsdaten = b_df[b_df['Kunde_Nr'] == int(kunde_nr)].to_dict(orient='records')

        return render(request, self.template_name, {
            'kunde_nr': kunde_nr,
            'bearbeitungsdaten': bearbeitungsdaten,
        })

    def post(self, request, *args, **kwargs):
        kunde_nr = kwargs.get('kunde_nr')
        _, b_df = get_data()

        # Add new bearbeitungsdaten
        new_data = {
            'Kunde_Nr': int(kunde_nr),
            'Kontaktdatum': request.POST.get('datum'),
            'Bemerkung_Kundenwünsche': request.POST.get('beschreibung'),
            'Kontaktweg': request.POST.get('status')
        }
        b_df = b_df._append(new_data, ignore_index=True)

        # Save the updated DataFrame back to the Excel file
        with pd.ExcelWriter('Kundendaten_Bearbeitungsdaten_200.xlsx', mode='a', if_sheet_exists='replace') as writer:
            b_df.to_excel(writer, sheet_name='Bearbeitungsdaten', index=False)

        bearbeitungsdaten = b_df[b_df['Kunde_Nr'] == int(kunde_nr)].to_dict(orient='records')
        return render(request, self.template_name, {
            'kunde_nr': kunde_nr,
            'bearbeitungsdaten': bearbeitungsdaten,
        })

def import_data():
    df = pd.read_excel('Kundendaten_Bearbeitungsdaten_200.xlsx')
    b_df = pd.read_excel('Kundendaten_Bearbeitungsdaten_200.xlsx', sheet_name='Bearbeitungsdaten')

    df.columns = df.columns.str.replace(' ', '_')
    df.columns = df.columns.str.replace("-", "_")
    df.columns = df.columns.str.replace(".", "")

    b_df.columns = b_df.columns.str.replace(' ', '_')
    b_df.columns = b_df.columns.str.replace("-", "_")
    b_df.columns = b_df.columns.str.replace(".", "")
    b_df.columns = b_df.columns.str.replace(")", "")
    b_df.columns = b_df.columns.str.replace("(", "")

    # Convert the date columns to pandas datetime format
    df['Datum_Anfrage'] = pd.to_datetime(df['Datum_Anfrage'], format="%Y-%m-%d")
    df['Datum_Bestellung'] = pd.to_datetime(df['Datum_Bestellung'], format="%Y-%m-%d")
    df['Datum_Wiedervorlage'] = pd.to_datetime(df['Datum_Wiedervorlage'], format="%Y-%m-%d")

    # Rename columns to be compatible with dot notation


    print(
        list(df.columns)
    )

    return df, b_df

def evaluate_customer(row, weight_period=0.5, weight_changes_before=0.1, weight_changes_after=0.2, weight_information_method=0.2):
    period = (row['Datum_Wiedervorlage'] - row['Datum_Bestellung']).days
    changes_before = row['Anzahl_der_Änderungen_bis_zur_Bestellung']
    changes_after = row['Anzahl_der_Änderungswünsche_nach_der_Bestellung']
    information_method = row['Kontaktmöglichkeit_bei_Wiedervorlage']
    information_method_value = 0

    if information_method == 'Messe':
        information_method_value = 0.3
    elif information_method == 'Email':
        information_method_value = 0.2
    elif information_method == 'Website':
        information_method_value = 0.2

    norm_period = min(period/30, 1)
    norm_changes_before = min(changes_before/5, 1)
    norm_changes_after = min(changes_after/5, 1)

    evaluation = (weight_period * (1 - norm_period) +
                  weight_changes_before * (1 - norm_changes_before) +
                  weight_changes_after * (1 - norm_changes_after) +
                  weight_information_method * information_method_value)

    return evaluation

def filter_data(df, time_filter):
    today = datetime.today()

    if time_filter == 'last_year':
        start_date = today.replace(year=today.year - 1, month=1, day=1)
        end_date = today.replace(year=today.year - 1, month=12, day=31)
    elif time_filter == 'last_quarter':
        current_quarter = (today.month - 1) // 3 + 1
        start_month = 3 * (current_quarter - 2) + 1
        start_date = today.replace(month=start_month, day=1) - timedelta(days=1)
        end_date = today.replace(month=start_month + 2, day=1) - timedelta(days=1)
    elif time_filter == 'last_month':
        start_date = today.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)

    df = df[(df['Datum_Anfrage'] >= start_date) & (df['Datum_Anfrage'] <= end_date)]
    return df

def filter_custom_data(df, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = df[(df['Datum_Anfrage'] >= start_date) & (df['Datum_Anfrage'] <= end_date)]
    return df

def get_data():
    df, b_df = import_data()
    df['Evaluation'] = df.apply(evaluate_customer, axis=1)
    return df, b_df


class NewCustomerView(View):
    template_name = 'core/new_customer.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        df, _ = get_data()

        # Generate new Kunde_Nr
        if df.empty:
            new_kunde_nr = 1
        else:
            new_kunde_nr = df['Kunde_Nr'].max() + 1

        # Add new customer data
        new_customer = {
            'Kunde_Nr': new_kunde_nr,
            'Datum_Anfrage': request.POST.get('datum_anfrage'),
            'Datum_Bestellung': request.POST.get('datum_bestellung'),
            'Datum_Wiedervorlage': request.POST.get('datum_wiedervorlage'),
            'Anzahl_der_Änderungen_bis_zur_Bestellung': request.POST.get('aenderungen_vor_bestellung'),
            'Anzahl_der_Änderungswünsche_nach_der_Bestellung': request.POST.get('aenderungen_nach_bestellung'),
            'Erstinformation_über': request.POST.get('informationsweg'),
            'Kontaktmöglichkeit_bei_Wiedervorlage': request.POST.get('informationsweg'),

        }
        df = df._append(new_customer, ignore_index=True)


        # Save the updated DataFrame back to the Excel file
        try:
            with pd.ExcelWriter('Kundendaten_Bearbeitungsdaten_200.xlsx', mode='a',
                                if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name='Kundendaten', index=False)
            print("Customer created successfully")
        except Exception as e:
            print(f"Error saving customer: {e}")

        return redirect('home')

