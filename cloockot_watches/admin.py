from django.contrib import admin
from .models import Korisnik, Porudzbina

@admin.register(Korisnik)
class KorisnikAdmin(admin.ModelAdmin):
    list_display = ('korisnicko_ime', 'ime', 'prezime', 'email', 'telefon', 'broj_porudzbina')
    search_fields = ('korisnicko_ime', 'ime', 'prezime', 'email', 'telefon')
    list_filter = ('ime', 'prezime')
    
    def broj_porudzbina(self, obj):
        return obj.porudzbine.count()
    broj_porudzbina.short_description = 'Broj porudžbina'

@admin.register(Porudzbina)
class PorudzbinaAdmin(admin.ModelAdmin):
    list_display = ('id', 'korisnik_info', 'formatirani_artikli_display', 'datum', 'ukupno_display')
    search_fields = ('korisnik__korisnicko_ime', 'korisnik__ime', 'korisnik__prezime')
    list_filter = ('datum', 'korisnik')
    readonly_fields = ('datum', 'formatirani_artikli')
    fieldsets = (
        ('Osnovne informacije', {
            'fields': ('korisnik', 'datum', 'ukupno')
        }),
        ('Artikli', {
            'fields': ('formatirani_artikli', 'artikli'),
            'classes': ('collapse',)
        }),
    )
    
    def korisnik_info(self, obj):
        return f"{obj.korisnik.korisnicko_ime} ({obj.korisnik.ime} {obj.korisnik.prezime})"
    korisnik_info.short_description = 'Korisnik'
    
    def formatirani_artikli_display(self, obj):
        # Skraćena verzija za list display
        if not obj.artikli:
            return "Nema artikala"
        try:
            items = obj.artikli[:3]  # Prikaži samo prva 3 artikla
            result = []
            for art in items:
                result.append(f"{art.get('brend', '')} - {art.get('naziv', '')[:20]}...")
            return "; ".join(result)
        except:
            return str(obj.artikli)[:50] + "..."
    formatirani_artikli_display.short_description = 'Artikli'
    
    def ukupno_display(self, obj):
        return f"{obj.ukupno:,} RSD".replace(",", ".")
    ukupno_display.short_description = 'Ukupno'