from django import forms
from .models import Club,Membership
from django.contrib.auth import get_user_model

class ClubForm(forms.ModelForm):
    class Meta:
        model=Club
        fields=("name","description")


class AddMemberForm(forms.Form):
    
    email=forms.EmailField(label="member's email")
    role=forms.ChoiceField(
        choices=[
            (Membership.Role.MEMBER,'MEMBER'),
            (Membership.Role.TREASURER,'TREASURER')
        ]
    )

    def __init__(self,*args,club,**kwargs):
        super().__init__(*args,**kwargs)
        self.club=club

    def clean_email(self):
        email=self.cleaned_data["email"].strip()
        User=get_user_model()

        try:
            user=User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No this email , please ask them to register first")

        already_member=Membership.objects.filter(
            club=self.club,
            user=user
        ).exists()

        if already_member:
            raise forms.ValidationError("This user is already a member at here")

        self.user_to_add=user
        return email

    def save(self):
        return Membership.objects.create(
            club=self.club,
            user=self.user_to_add,
            role=self.cleaned_data["role"]
        )
        

