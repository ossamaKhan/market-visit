from django import forms
from hierarchy.models import FranchiseRecord
from .models import MarketVisit


class MarketVisitForm(forms.ModelForm):
    franchise = forms.ModelChoiceField(
        queryset=FranchiseRecord.objects.none(),
        required=True,
        empty_label="— Select a franchise —",
        label="Franchise (FR ID)",
    )
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_latitude'}),
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_longitude'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and getattr(user, 'email', ''):
            queryset = FranchiseRecord.objects.filter(
                email__iexact=user.email
            ).order_by('region', 'fr_id')
        else:
            queryset = FranchiseRecord.objects.none()

        # If editing an existing visit whose franchise isn't in that set
        # (e.g. hierarchy ownership changed since), still include it so
        # the saved value doesn't silently disappear from the form.
        instance = kwargs.get('instance')
        if instance is not None and instance.franchise_id:
            queryset = queryset | FranchiseRecord.objects.filter(pk=instance.franchise_id)
            queryset = queryset.distinct()

        self.fields['franchise'].queryset = queryset

    class Meta:
        model = MarketVisit
        fields = [
            'franchise', 'new_or_existing',
            'name', 'evc', 'visit_type', 'bvs', 'bvs_imei', 'rso_visit', 'latitude', 'longitude',
            'load_stock_range', 'psim_stock', 'npsim_stock', 'mbb_stock',
            'zong_avg_loading', 'zong_avg_sim_sales', 'jazz_avg_loading', 'jazz_avg_sim_sales',
            'fascia_zong', 'fascia_ufone', 'fascia_jazz', 'avh', 'pos',
            'promo_awareness', 'bundle_awareness',
            'fca_commitment', 'mnp_commitment',
            'comments',
            'photo', 'photo2',
        ]
        widgets = {
            'evc': forms.TextInput(attrs={'placeholder': 'e.g. 923001234567'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Any additional notes about this visit...'}),
        }