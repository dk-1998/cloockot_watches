from django.db import models
from django.core.validators import RegexValidator
from django.core.files.storage import default_storage

class Korisnik(models.Model):
    ime = models.CharField(max_length=30)
    prezime = models.CharField(max_length=30)
    korisnicko_ime = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    telefon = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{9,15}$', message="Unesite validan broj telefona.")]
    )
    lozinka = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.korisnicko_ime} ({self.ime} {self.prezime})"
    
    class Meta:
        verbose_name = "Korisnik"
        verbose_name_plural = "Korisnici"

class Porudzbina(models.Model):
    korisnik = models.ForeignKey(Korisnik, on_delete=models.CASCADE, related_name='porudzbine')
    datum = models.DateTimeField(auto_now_add=True)
    artikli = models.JSONField(help_text="Lista artikala u JSON formatu")
    ukupno = models.IntegerField(help_text="Ukupna cena u RSD")

    def __str__(self):
        return f"Porudžbina #{self.id} – {self.korisnik.korisnicko_ime} ({self.datum.strftime('%d.%m.%Y %H:%M')})"
    
    def formatirani_artikli(self):
        """Vraća formatiran string sa artiklima za admin panel"""
        if not self.artikli:
            return "Nema artikala"
        
        try:
            result = []
            for i, art in enumerate(self.artikli, 1):
                result.append(f"{i}. {art.get('brend', '')} - {art.get('naziv', '')} x{art.get('kolicina', 1)} = {art.get('ukupno_za_artikal', 0)} RSD")
            return "\n".join(result)
        except:
            return str(self.artikli)
    
    formatirani_artikli.short_description = "Artikli"
    
    class Meta:
        verbose_name = "Porudžbina"
        verbose_name_plural = "Porudžbine"
        ordering = ['-datum']
        
    

class Sat(models.Model):
    # postojeći field-ovi
    slika = models.ImageField(upload_to='satovi/')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Možete dodati automatsku optimizaciju slika
        # koristeći Pillow biblioteku