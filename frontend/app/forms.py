from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo Electrónico',
            'id': 'email-input'
        }),
        label="Correo Electrónico"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'id': 'password-input'
        }),
        label="Contraseña"
    )
