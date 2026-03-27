from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import RegistracijaForm, PrijavaForm
import json
from .models import Korisnik, Porudzbina
from django.shortcuts import redirect
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html
from django.core.mail import EmailMultiAlternatives
from django.core.mail import EmailMessage
from django.core.files.images import get_image_dimensions
from email.mime.image import MIMEImage
from django.conf import settings

from django.http import JsonResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from django.core.mail import EmailMultiAlternatives
#from django.template.loader import render_to_string
#from django.utils.html import strip_tags

@csrf_exempt
def posalji_email(request):
    if request.method == "POST":
        try:
            # Obradi podatke...
            
            subject = "Upit sa Cloockot sajta"
            body_text = f"Email: {email}\nTelefon: {telefon}\nPoruka: {poruka}"
            
            body_html = f"""
            <html>
            <body>
                <h2>Nov upit sa Cloockot sajta</h2>
                <p><b>Email pošiljaoca:</b> {email}</p>
                <p><b>Telefon:</b> {telefon}</p>
                <p><b>Poruka:</b><br>{poruka}</p>
            </body>
            </html>
            """

            # KORIGOVAN DEO - dodajemo DEFAULT_FROM_EMAIL
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,  # ← OVO JE BITNO
                to=["cloockot@gmail.com"],
                reply_to=[email],
            )
            msg.attach_alternative(body_html, "text/html")

            if slika:
                # Provera veličine slike
                if slika.size > 5 * 1024 * 1024:
                    return JsonResponse(
                        {'error': 'Slika je prevelika. Maksimalna veličina je 5MB.'},
                        status=400
                    )
                
                # Dodaj sliku
                img_data = slika.read()
                img = MIMEImage(img_data)
                img.add_header('Content-ID', '<slika1>')
                img.add_header('Content-Disposition', 'inline', filename=slika.name)
                msg.attach(img)
                
                # Ažuriraj HTML da prikaže sliku
                updated_html = body_html + f'''
                <p><b>Uploadovana slika:</b><br>
                <img src="cid:slika1" style="max-width:400px;border:1px solid #ccc;border-radius:8px">
                </p>
                '''
                msg.attach_alternative(updated_html, "text/html")

            # Pošalji email sa try-except
            try:
                msg.send(fail_silently=False)  # fail_silently=False da bismo videli grešku
                return JsonResponse({'success': True, 'message': 'Email je uspešno poslat.'})
            except Exception as e:
                print(f"SMTP greška: {str(e)}")  # Ovo će ti pomoći da vidiš tačnu grešku
                return JsonResponse(
                    {'error': f'Greška pri slanju emaila: {str(e)}'},
                    status=500
                )

        except Exception as e:
            print(f"Generalna greška: {str(e)}")
            return JsonResponse(
                {'error': f'Došlo je do greške: {str(e)}'},
                status=500
            )

    return JsonResponse({'error': 'Metoda nije dozvoljena.'}, status=405)


# Osnovne stranice
def index(request): return render(request, 'cloockot_watches/index.html')
def onama(request): return render(request, 'cloockot_watches/onama.html')
def satovi(request):
    # Proveri da li je korisnik ulogovan
    ulogovan = 'korisnicko_ime' in request.session
    
    # Dodajte ovaj kontekst kako biste mogli da ga koristite u template-u
    context = {
        'ulogovan': ulogovan,
    }
    
    return render(request, 'cloockot_watches/satovi.html', context)
def kontakt(request): return render(request, 'cloockot_watches/kontakt.html')

# Registracija
def registracija(request):
    if request.method == 'POST':
        form = RegistracijaForm(request.POST)
        if form.is_valid():
            korisnik = form.save(commit=False)
            korisnik.lozinka = make_password(form.cleaned_data['lozinka'])
            korisnik.save()
            
            # NE AUTOMATSKI LOGUJ KORISNIKA
            # request.session['korisnik_id'] = korisnik.id
            # request.session['korisnicko_ime'] = korisnik.korisnicko_ime
            
            # Dodaj poruku za uspešnu registraciju
            messages.success(request, f"Uspešno ste se registrovali kao {korisnik.korisnicko_ime}! Sada se možete prijaviti.")
            
            # Preusmeri na stranicu za prijavu
            return redirect('prijava')
    else:
        form = RegistracijaForm()
    
    return render(request, 'cloockot_watches/registracija.html', {'form': form})

# Prijava (ostaje ista, ali možete dodati poruku)
def prijava(request):
    if request.method == 'POST':
        form = PrijavaForm(request.POST)
        if form.is_valid():
            korisnicko_ime = form.cleaned_data['korisnicko_ime']
            lozinka = form.cleaned_data['lozinka']
            next_url = request.POST.get('next')  # 👈 BITNO

            try:
                korisnik = Korisnik.objects.get(korisnicko_ime=korisnicko_ime)
                if check_password(lozinka, korisnik.lozinka):
                    request.session['korisnik_id'] = korisnik.id
                    request.session['korisnicko_ime'] = korisnik.korisnicko_ime
                    messages.success(request, f"Dobrodošli {korisnik.korisnicko_ime}!")

                    # 👇 AKO POSTOJI next → VRATI TAMO
                    if next_url:
                        return redirect('next_url')

                    # fallback
                    return redirect('satovi')
                else:
                    messages.error(request, "Neispravna lozinka.")
            except Korisnik.DoesNotExist:
                messages.error(request, "Korisnik ne postoji.")
    else:
        form = PrijavaForm()

    return render(request, 'cloockot_watches/prijava.html', {'form': form})


# Odjava
def odjava(request):
    request.session.flush()
    return redirect('index')

# Checkout
# Checkout

def checkout(request):
    if not request.session.get('korisnicko_ime'):
        return JsonResponse({'error': 'Morate biti ulogovani da biste nastavili sa plaćanjem.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            korpa = data.get('cart', [])
            
            korisnicko_ime = request.session['korisnicko_ime']
            try:
                korisnik = Korisnik.objects.get(korisnicko_ime=korisnicko_ime)
            except Korisnik.DoesNotExist:
                return JsonResponse({'error': 'Korisnik ne postoji.'}, status=400)
            
            ukupno = 0
            artikli_lista = []
            
            for artikal in korpa:
                cena = int(artikal['price'])
                kolicina = int(artikal.get('qty', 1))
                ukupno += cena * kolicina
                
                artikli_lista.append({
                    'id': artikal['id'],
                    'naziv': artikal['title'],
                    'brend': artikal['brand'],
                    'cena': cena,
                    'kolicina': kolicina,
                    'ukupno_za_artikal': cena * kolicina
                })
            
            porudzbina = Porudzbina.objects.create(
                korisnik=korisnik,
                artikli=artikli_lista,
                ukupno=ukupno
            )
            
            # ========== SLANJE EMAIL-A ==========
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            
            # KORIGUJTE OVAJ DEO: 'datum' umesto 'datum_narucivanja'
            email_context = {
                'order_id': porudzbina.id,
                'order_date': porudzbina.datum.strftime('%d.%m.%Y %H:%M'),  # ← OVO JE ISPRAVLJENO
                'customer': {
                    'username': korisnik.korisnicko_ime,
                    'email': korisnik.email,
                    'id': korisnik.id,
                },
                'items': artikli_lista,
                'total': ukupno,
            }
            
            # HTML verzija iz template-a (ako ga koristite)
            # Ako nemate template, koristite inline HTML kao što je u prethodnom odgovoru
            try:
                html_content = render_to_string('emails/order_confirmation_admin.html', email_context)
            except:
                # Fallback ako template ne postoji - koristite inline HTML
                html_content = f"""
                <html>
                <body>
                    <h2>🚀 Nova porudžbina #{porudzbina.id}</h2>
                    <p><strong>Datum:</strong> {email_context['order_date']}</p>
                    <p><strong>Korisnik:</strong> {korisnik.korisnicko_ime}</p>
                    <p><strong>Email:</strong> {korisnik.email}</p>
                    
                    <h3>Stavke:</h3>
                    <table border="1" cellpadding="8" style="border-collapse: collapse;">
                        <tr>
                            <th>Proizvod</th><th>Brend</th><th>Cena</th><th>Količina</th><th>Ukupno</th>
                        </tr>
                """
                
                for item in artikli_lista:
                    html_content += f"""
                        <tr>
                            <td>{item['naziv']}</td>
                            <td>{item['brend']}</td>
                            <td>{item['cena']:,} RSD</td>
                            <td>{item['kolicina']}</td>
                            <td>{item['ukupno_za_artikal']:,} RSD</td>
                        </tr>
                    """
                
                html_content += f"""
                    </table>
                    <h3>UKUPNO: {ukupno:,} RSD</h3>
                    <hr>
                    <p><em>Porudžbina je automatski sačuvana u sistemu.</em></p>
                </body>
                </html>
                """
            
            text_content = strip_tags(html_content)
            subject = f'🚀 Nova porudžbina #{porudzbina.id} - {korisnik.korisnicko_ime}'
            
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['Kamm1997@gmail.com'],
                    reply_to=[korisnik.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=True)
                print(f"✅ Email porudžbine #{porudzbina.id} poslat na cloockot.probniemail@gmail.com")
            except Exception as e:
                print(f"⚠️ Email nije poslat za porudžbinu #{porudzbina.id}: {e}")
            # ========== KRAJ EMAIL DELA ==========
            
            return JsonResponse({
                'success': True, 
                'message': 'Porudžbina je uspešno kreirana.',
                'order_id': porudzbina.id,
                'total': ukupno
            })
            
        except Exception as e:
            print(f"Greška u checkout: {e}")  # Dodajte za debugging
            return JsonResponse({'error': f'Greška: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': 'Zahtev mora biti POST.'}, status=405)
