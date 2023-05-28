from flask import Flask,url_for,redirect,render_template,request,session,flash
import pyodbc
import smtplib
from decimal import Decimal
from datetime import datetime
app = Flask(__name__)

#configuration de la base de données
server = 'ahmed'
database = 'ecommerce'
username = ''
password = ''
conn_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
conn = pyodbc.connect(conn_string)
cursor = conn.cursor()
@app.route('/')
def index():
    title="Log In"
    return render_template("login.html",title=title)
@app.route('/register')
def register():
    return render_template("signup.html")
@app.route('/traitement_register', methods=['POST'])
def traitement_register():
    # Récupérer les données du formulaire d'inscription
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    password = request.form['password']
    adresse = request.form['adresse']
    telephone = request.form['telephone']
    cursor.execute("INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, adresse, telephone) VALUES (?, ?, ?, ?, ?, ?)", nom, prenom, email, password, adresse, telephone)
    conn.commit()
    message = "Inscription effectuée avec succès !"
    flash(message)
    return redirect('/')
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method=='GET':
         message = request.args.get('message')
    title="Contact"
    return render_template("contact.html",title=title,message=message)
@app.route('/accueil')
def accueil():
     title="MonSiteEcommerce - Accueil"
     return render_template("accueil.html",title=title)

@app.route('/produits')
def produits():
    sql="select * from produits"
    resultat=cursor.execute(sql)
    products=resultat.fetchall()
    return render_template("produits.html",products=products)
    conn.close()
@app.route('/moreinfo')
def info():
    id = request.args['id']
    cursor.execute('SELECT * FROM produits WHERE id = ?',id)
    products=cursor.fetchall()
    return render_template("moreinfo.html",product=products,id=id)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username =request.form['username']
        password =request.form['password']
        cursor.execute("SELECT * FROM utilisateurs WHERE email = ? AND mot_de_passe= ?", (username,password))
        row=cursor.fetchall()
        if row :
            for user in row:
                session['id']=user[0]
                session['name']=user[1]
            return redirect("/accueil")
        else:
            return redirect("/")
app.secret_key = 'votre_clé_secrète_unique_et_secrete'
@app.route('/deconnexion')
def deconnexion():
    # Supprimer les informations de session
    session.clear()
    # Rediriger vers la page d'accueil ou une autre page après la déconnexion
    return redirect('/')
@app.route('/panier')
def afficher_panier():
    # Récupérer les données du panier depuis la base de données
    id=session['id']
    cursor.execute("select panier.total,panier.id,panier.quantite,Produits.prix,Produits.nom,Produits.img from panier inner join Produits on panier.produit_id=Produits.id where panier.utilisateur_id=?",(id))
    panier = cursor.fetchall()
    # Rendre le template HTML en affichant les données du panier
    return render_template('panier.html', panier=panier)
    
@app.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    id = session['id']
    id_produit = request.args['id_pro']
    cursor.execute('SELECT prix FROM produits WHERE id=?', id_produit)
    rows = cursor.fetchall()
    prix = None
    for row in rows:
        prix = row[0]  # Récupérer la valeur du prix à partir du premier élément du tuple
    if prix is not None:
        prix = float(prix)

    if request.method == 'POST':
        qte = request.form['quantity']
        qte = float(qte)
        total = prix * qte
        cursor.execute("INSERT INTO panier (utilisateur_id, produit_id, quantite, total) VALUES (?, ?, ?, ?)", (id, id_produit, qte, total))
        conn.commit()
    return redirect('/panier')

@app.route('/delete_panier')
def deletepanier():
    id_panier = request.args['id_panier']
    cursor.execute('delete from panier where id=?',id_panier)
    conn.commit()
    return redirect('/panier')
@app.route('/update_panier', methods=['GET', 'POST'])
def update_panier():
    id_panier = request.args['id_panier']
    prix = 0
    prix = float(request.args['prix'])

    if request.method == 'POST':
            qte = float(request.form['quantity'])
            total = qte * prix
            cursor.execute('UPDATE panier SET quantite=?, total=? WHERE id=?', (qte, total, id_panier))
            conn.commit()
            return redirect('/panier')

    return render_template("updateqte.html", id_panier=id_panier, prix=prix)

@app.route('/valider_commande')
def valider_commande():
    id=session['id']
    cursor.execute('SELECT * FROM panier WHERE utilisateur_id = ?', id)
    rows=cursor.fetchall()
    for panier in rows:
          cursor.execute('INSERT INTO achats (date, produit_id, total, utilisateur_id, qte) VALUES (sysdatetime(), ?, ?, ?, ?)', (panier.produit_id, panier.total, id, panier.quantite))
    cursor.execute('delete from  panier  where  utilisateur_id =?',id)
    conn.commit()
    return render_template('valider.html')  
@app.route('/annuler_commande')
def annuler_commande():
    id=session['id']
    cursor.execute('delete from  panier  where  utilisateur_id =?',id)
    return redirect('/panier')
@app.route('/achats')
def meschats():
    id=session['id']
    cursor.execute('select achats.date,achats.total,Produits.nom,achats.qte,Produits.prix from achats,Produits where achats.produit_id=Produits.id and achats.utilisateur_id=?',id)
    achats=cursor.fetchall()
    return render_template("mesachats.html",achats=achats)
@app.route('/envoyer_email', methods=['GET', 'POST'])
def envoyer_email():
    if request.method == 'POST':
        destinataire = request.form['email']
        sujet = request.form['name']
        contenu = request.form['message']

        # Configuration du serveur SMTP
        serveur_smtp = smtplib.SMTP('smtp.gmail.com', 587)
        serveur_smtp.starttls()
        serveur_smtp.login('salmaanoubl@gmail.com', 'ivkklzdeawaupmbv')

        message = f"Subject: {sujet}\n\n{contenu}"

        # Envoi de l'e-mail
        serveur_smtp.sendmail('votre_adresse_email', destinataire, message)

        # Fermeture de la connexion SMTP
        serveur_smtp.quit()

        message="E-mail envoyé avec succès !"
        return redirect(url_for('contact', message=message))
@app.route('/tendances')
def tendances():
    # Récupérer les données des tendances depuis la base de données
    cursor.execute('SELECT * FROM nouveaute')
    tendances = cursor.fetchall()

    # Passer les données des tendances au template
    return render_template('tendance.html', tendances=tendances)
...

@app.route('/promotions')
def promotions():
    cursor.execute("SELECT Produits.nom, promotions.* FROM produits, promotions WHERE Produits.id = promotions.produit_id AND date_debut <= SYSDATETIME() AND date_fin >= SYSDATETIME()")
    promotions = cursor.fetchall()
    return render_template('promotions.html', promotions=promotions)


if __name__ == "__main__":
    app.run(debug=True)