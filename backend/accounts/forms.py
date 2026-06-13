from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={'placeholder': 'Parol kiriting'}),
        min_length=6,
        error_messages={'min_length': 'Parol kamida 6 ta belgi bo\'lishi kerak'}
    )
    password2 = forms.CharField(
        label='Parolni tasdiqlang',
        widget=forms.PasswordInput(attrs={'placeholder': 'Parolni qayta kiriting'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'phone', 'telegram_id']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Isminiz'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Familiyangiz'}),
            'username': forms.TextInput(attrs={'placeholder': 'Foydalanuvchi nomi'}),
            'phone': forms.TextInput(attrs={'placeholder': '+998901234567'}),
            'telegram_id': forms.NumberInput(attrs={'placeholder': 'Telegram ID (ixtiyoriy)'}),
        }
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'username': 'Foydalanuvchi nomi',
            'phone': 'Telefon raqam',
            'telegram_id': 'Telegram ID',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone.startswith('+') or not phone[1:].isdigit():
            raise forms.ValidationError("Telefon raqam noto'g'ri formatda. Misol: +998901234567")
        if len(phone) < 10:
            raise forms.ValidationError("Telefon raqam juda qisqa.")
        return phone

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val:
            raise forms.ValidationError("Ism majburiy.")
        if len(val) < 2:
            raise forms.ValidationError("Ism kamida 2 ta harf bo'lishi kerak.")
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val:
            raise forms.ValidationError("Familiya majburiy.")
        if len(val) < 2:
            raise forms.ValidationError("Familiya kamida 2 ta harf bo'lishi kerak.")
        return val

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar bir-biriga mos emas.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Foydalanuvchi nomi',
        widget=forms.TextInput(attrs={'placeholder': 'Foydalanuvchi nomi'})
    )
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={'placeholder': 'Parol'})
    )
