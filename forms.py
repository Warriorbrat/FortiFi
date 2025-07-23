from django import forms
import joblib

# Load feature names from the trained model
model, feature_names = joblib.load('model/trained_model.pkl')

# Define how many fields are considered basic
BASIC_FIELDS = feature_names[:10]  # Adjust this range as needed

class ManualInputForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ManualInputForm, self).__init__(*args, **kwargs)

        for field in feature_names:
            if field in BASIC_FIELDS:
                # BASIC fields are required and initially empty
                self.fields[field] = forms.FloatField(
                    required=True,
                    label=field,
                    widget=forms.NumberInput(attrs={'class': 'form-control'})
                )
            else:
                # ADVANCED fields are optional and default to 0
                self.fields[field] = forms.FloatField(
                    required=False,
                    label=field,
                    initial=0,
                    widget=forms.NumberInput(attrs={'class': 'form-control'})
                )

    def get_basic_fields(self):
        return [self[field] for field in BASIC_FIELDS]

    def get_advanced_fields(self):
        return [self[field] for field in self.fields if field not in BASIC_FIELDS]


class FileUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
