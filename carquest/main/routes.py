from flask import Blueprint, render_template, request, redirect, url_for, session, flash,current_app, Flask
from flask import send_file
from flask import Response
from extensions import mongo
from bson import ObjectId
from werkzeug.utils import secure_filename

from datetime import datetime

from flask import jsonify,render_template_string, make_response
import os
from fpdf import FPDF

from pymongo.errors import PyMongoError

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Query the MongoDB collection for the user with the provided email
        user = mongo.db.user.find_one({'email': email})
        
        if user and user['mdp'] == password:  # Check if user exists and password is correct
            session['email'] = email  # Store user's email in session
            session['role'] = user['role']  # Store user's role in session
            return redirect(url_for('main.dashboard'))  # Redirect to dashboard or any other page
        else:
            # Authentication failed, render login page with error message
            flash("Email or password is incorrect", "error")
            return render_template('login.html')
    else:
        return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    if 'email' in session:
        # Query the MongoDB collection for the user with the logged-in email
        user = mongo.db.user.find_one({'email': session['email']})
        
        # Check if the user exists and has a role
        if user and 'role' in user:
            if user['role'] == 'admin':

                # Compter le nombre de voitures, clients et managers
                car_count = mongo.db['car'].count_documents({})
                client_count = mongo.db['client'].count_documents({})
                manager_count = mongo.db['manager'].count_documents({})
                reservations_count = mongo.db['reservations'].count_documents({})

                return render_template('admin/admin_dashboard.html', car_count=car_count, 
                                       client_count=client_count, manager_count=manager_count, 
                                       reservations_count=reservations_count)
            elif user['role'] == 'manager':

                # Compter le nombre de voitures, clients et managers
                car_count = mongo.db['car'].count_documents({})
                client_count = mongo.db['client'].count_documents({})
                manager_count = mongo.db['manager'].count_documents({})
                reservations_count = mongo.db['reservations'].count_documents({})
                reservations_en_cours_count = mongo.db['reservations'].count_documents({'statut': 'reserved'})
                reservations_acceptees_count = mongo.db['reservations'].count_documents({'statut': 'confirmé'})
                reservations_refusees_count = mongo.db['reservations'].count_documents({'statut': 'refusé'})

                return render_template('manager/manager_dashboard.html', car_count=car_count, 
                                       client_count=client_count, manager_count=manager_count, 
                                       reservations_count=reservations_count,
                                       reservations_en_cours_count=reservations_en_cours_count,
                                       reservations_acceptees_count=reservations_acceptees_count,
                                       reservations_refusees_count=reservations_refusees_count)
        
        # If user has no role or unknown role, redirect to login page
        flash("You are not authorized to access this page", "error")
        return redirect(url_for('main.login'))
    else:
        # If user is not logged in, redirect to login page
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))

@main.route('/showManager')
def show_manager():
    if 'email' in session:
        # Retrieve manager data from MongoDB
        managers = mongo.db.manager.find()
        return render_template('admin/show_manager.html', managers=managers)
    else:
        # If user is not logged in, redirect to login page
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))
"""
@main.route('/edit_manager/<id>', methods=['GET', 'POST'])
def edit_manager(id):
    if request.method == 'POST':
        # Handle the POST request to update manager data
        updated_data = {
            'email': request.form.get('email'),
            'nom': request.form.get('nom'),
            'prenom': request.form.get('prenom')
        }
        
        # Retrieve the existing manager document
        existing_manager = mongo.db.manager.find_one({'_id': ObjectId(id)})
        old_email = existing_manager['email']
        
        # Update the manager collection
        mongo.db.manager.update_one({'_id': ObjectId(id)}, {'$set': updated_data})

        # Update the user collection
        mongo.db.user.update_one(
            {'email': old_email, 'role': 'manager'},
            {'$set': updated_data}
        )

        flash('Manager modifié avec succés !', 'success')
        return redirect(url_for('main.show_manager'))
    else:
        # Display the form with existing data
        manager = mongo.db.manager.find_one({'_id': ObjectId(id)})
        return render_template('admin/edit_manager.html', manager=manager)
"""

@main.route('/edit_manager/<id>', methods=['GET', 'POST'])
def edit_manager(id):
    if request.method == 'POST':
        updated_data = {
            'email': request.form.get('email'),
            'nom': request.form.get('nom'),
            'prenom': request.form.get('prenom')
        }

        try:
            existing_manager = mongo.db.manager.find_one({'_id': ObjectId(id)})
            old_email = existing_manager['email']
            
            # Update the manager collection
            mongo.db.manager.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
            
            # Update the user collection
            mongo.db.user.update_one(
                {'email': old_email, 'role': 'manager'},
                {'$set': updated_data}
            )

            flash('Manager modifié avec succès !', 'success')
            print("Redirection vers show_manager")  # Pour vérifier que cette ligne est atteinte
            return redirect(url_for('main.show_manager'))
        except Exception as e:
            flash(f'Une erreur s\'est produite: {str(e)}', 'danger')
            return redirect(url_for('main.edit_manager', id=id))
    else:
        manager = mongo.db.manager.find_one({'_id': ObjectId(id)})
        return render_template('admin/edit_manager.html', manager=manager)

@main.route('/delete_manager/<id>', methods=['POST'])
def delete_manager(id):
    mongo.db.manager.delete_one({'_id': ObjectId(id)})
    flash('Manager deleted successfully!', 'success')
    return redirect(url_for('main.show_manager'))

def get_next_manager_id():
    sequence_document = mongo.db.counterm.find_one_and_update(
        {'_id': 'manager'},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['seq']

@main.route('/add_manager', methods=['GET', 'POST'])
def add_manager():
    if request.method == 'POST':
        email = request.form['email']
        nom = request.form['nom']
        prenom = request.form['prenom']
        password = request.form['mdp']  # Ensure the password field name is correct
        manager_id = get_next_manager_id()  # Assuming this function is correctly fetching or incrementing ID

        existing_user = mongo.db.user.find_one({'email': email})
        if existing_user:
            flash('A user with the same email already exists!', 'error')
            return render_template('admin/add_manager.html')

        hashed_password = password
        user_data = {
            'email': email,
            'nom': nom,
            'prenom': prenom,
            'mdp': hashed_password,
            'role': 'manager'
        }
        manager_data = {
            'id': manager_id,  # Using a unique identifier for managers
            'email': email,
            'nom': nom,
            'prenom': prenom
        }

        # Insert data into user and manager collections
        mongo.db.user.insert_one(user_data)
        mongo.db.manager.insert_one(manager_data)

        flash('Manager added successfully!', 'success')
        return redirect(url_for('main.show_manager'))

    return render_template('admin/add_manager.html')

@main.route('/logout')
def logout():
    session.clear()  # This clears all data stored in session
    flash('You have been logged out.', 'info')  # Optional: Flash a message to the user
    return redirect(url_for('main.login'))  # Redirect to login page
###CARS ###
@main.route('/show_car')
def show_car():
    if 'email' in session:
        # Retrieve all cars from MongoDB
        cars = mongo.db.car.find()
        cars_list = []
        for car in cars:
            if 'image' in car and car['image']:
                car['image_url'] = url_for('static', filename=f'car/{car["image"]}')
            else:
                car['image_url'] = url_for('static', filename='car/default.jpg')  # Default image if none is specified
            cars_list.append(car)
        return render_template('manager/show_car.html', cars=cars_list)
    else:
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))

def get_next_sequence(car):
    sequence_document = mongo.db.counters.find_one_and_update(
        {'_id': car},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['seq']





@main.route('/edit_car/<id>', methods=['GET', 'POST'])
def edit_car(id):
    if request.method == 'POST':
        updated_data = {}
        field_names = ['status', 'fuel', 'km', 'couleur', 'marque', 'modele', 'prix']
        for field in field_names:
            if request.form.get(field):
                updated_data[field] = request.form.get(field)

        if updated_data:
            update_result = mongo.db.car.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
            if update_result.modified_count == 1:
                flash('Car updated successfully!', 'success')
            else:
                flash('No changes were made.', 'info')
        else:
            flash('No valid data provided for update.', 'error')

        return redirect(url_for('main.show_car'))
    else:
        car = mongo.db.car.find_one({'_id': ObjectId(id)})
        if not car:
            flash('No car found with the given ID.', 'error')
            return redirect(url_for('main.show_car'))
        return render_template('manager/edit_car.html', car=car)


@main.route('/delete_car/<id>', methods=['POST'])
def delete_car(id):
    mongo.db.car.delete_one({'_id': ObjectId(id)})
    flash('Car deleted successfully!', 'success')
    return redirect(url_for('main.show_car'))


# Helper function to increment car ID
def get_next_sequence(name):
    sequence_document = mongo.db.counters.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['seq']

@main.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        if 'email' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('main.login'))

        # Retrieve form data
        status = request.form.get('status')
        fuel = request.form.get('fuel')
        km = request.form.get('km')
        couleur = request.form.get('couleur')
        marque = request.form.get('marque')
        modele = request.form.get('modele')
        prix = request.form.get('prix')
        
        # Handle file upload
        image = request.files['image']
        filename = secure_filename(image.filename)
        if filename:
            file_path = os.path.join(current_app.static_folder, 'car', filename)
            image.save(file_path)

        # Auto-increment car ID
        car_id = get_next_sequence('car_id')
        
        # Insert car data into MongoDB
        car_data = {
            'id': car_id,
            'status': status,
            'fuel': fuel,
            'km': km,
            'couleur': couleur,
            'marque': marque,
            'modele': modele,
            'prix': prix,
            'image': filename
        }
        mongo.db.car.insert_one(car_data)
       # flash('Car added successfully!', 'success')
       # return redirect(url_for('main.show_car'))

    return render_template('manager/add_car.html')


#########""""""""""""""""******CLIENTS 
@main.route('/show_client')
def show_client():
    if 'email' in session:
        # Retrieve all clients from MongoDB
        clients = mongo.db['client'].find()

        client_list = []  # List to hold client data with modifications if necessary
        for client in clients:
            if 'photo' in client and client['photo']:
                client['photo_url'] = url_for('static', filename=f'client_photos/{client["photo"]}')
            else:
                client['photo_url'] = url_for('static', filename='client_photos/default.jpg')  # Default photo if none specified
            client_list.append(client)
        return render_template('manager/show_client.html', clients=client_list)
    else:
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))
    

def get_next_client_sequence(client_id):
    sequence_document = mongo.db.client_counters.find_one_and_update(
        {'_id': 'client_id'},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document['seq']

@main.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        if 'email' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('main.login'))

        # Retrieve form data
        email = request.form.get('email')
        mdp = request.form.get('mdp')
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        photo = request.files['photo']
        telephone = request.form.get('telephone')
        cin = request.form.get('cin')
        adresse = request.form.get('adresse')
        
        # Handle file upload for photo
        filename = secure_filename(photo.filename)
        if filename:
            file_path = os.path.join(current_app.static_folder, 'client_photos', filename)
            photo.save(file_path)

        # Auto-increment client ID
        client_id = get_next_client_sequence('client_id')

        # Insert client data into MongoDB
        client_data = {
            'id': client_id,
            'email': email,
            'mdp': mdp,
            'nom': nom,
            'prenom': prenom,
            'photo': filename,
            'telephone': telephone,
            'cin': cin,
            'adresse': adresse
        }
        mongo.db['client'].insert_one(client_data)
        flash('Client added successfully!', 'success')
        return redirect(url_for('main.show_client'))

    return render_template('manager/add_client.html')


@main.route('/edit_client/<id>', methods=['GET', 'POST'])
def edit_client(id):
    # Check if the request method is POST
    if request.method == 'POST':
        # Update the client data based on the form inputs
        updated_data = {}
        field_names = ['email', 'nom', 'prenom', 'telephone', 'cin', 'adresse', 'photo']  # Add any additional fields here
        for field in field_names:
            if request.form.get(field):
                updated_data[field] = request.form.get(field)

        if updated_data:
            # Update the client data in the MongoDB collection
            update_result = mongo.db['client'].update_one({'_id': ObjectId(id)}, {'$set': updated_data})
            if update_result.modified_count == 1:
                flash('Client updated successfully!', 'success')
            else:
                flash('No changes were made.', 'info')
        else:
            flash('No valid data provided for update.', 'error')

        # Redirect to the client list page
        return redirect(url_for('main.show_client'))
    else:
        # If the request method is GET, retrieve the client data for editing
        client = mongo.db['client'].find_one({'_id': ObjectId(id)})
        if not client:
            flash('No client found with the given ID.', 'error')
            return redirect(url_for('main.show_client'))

        # Render the edit client template with the client data
        return render_template('manager/edit_client.html', client=client)

@main.route('/reserve_car', methods=['GET', 'POST'])
def reserve_car():
    if 'email' not in session:
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        # Process the reservation form submission
        id_client = request.form.get('id_client')
        id_voiture = request.form.get('id_voiture')
        dateDebut = request.form.get('dateDebut')
        dateFin = request.form.get('dateFin')
        reservation_id = get_next_sequence('reservation_id')

        # Insert the reservation data into MongoDB
        reservation_data = {
            'id_reservation': reservation_id,
            'dateDebut': dateDebut,
            'dateFin': dateFin,
            'id_client': id_client,
            'id_voiture': id_voiture,
            'statut': 'reserved'  # assuming the initial status
        }
        mongo.db.reservations.insert_one(reservation_data)
        flash('Reservation added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    # Retrieve available cars and clients to populate the form dropdowns
    available_cars = mongo.db.car.find({'status': 'available'})
    clients = mongo.db['client'].find()
    return render_template('manager/Reserver_voiture.html', cars=available_cars, clients=clients)

@main.route('/show_reservations')
def show_reservations():
    if 'email' not in session:
        flash("Please log in to access this page", "error")
        return redirect(url_for('main.login'))

    # Fetch all reservations
    reservations = mongo.db.reservations.find()

    reservation_details = []
    for reservation in reservations:
        # Fetch the client data
        client = mongo.db['client'].find_one({'_id': ObjectId(reservation['id_client'])})
        # Fetch the car data
        car = mongo.db.car.find_one({'_id': ObjectId(reservation['id_voiture'])})

        # Append the detailed reservation info to the list
        reservation_details.append({
            'id_reservation': reservation['id_reservation'],
            'dateDebut': reservation['dateDebut'],
            'dateFin': reservation['dateFin'],
            'client': client,
            'car': car,
            'statut': reservation['statut']
        })

    # Pass the detailed reservations to the template
    return render_template('manager/reservation.html', reservations=reservation_details)


#SEARCH 

@main.route('/search_managers')
def search_managers():
    search_term = request.args.get('search', '')
    filtered_managers = mongo.db.manager.query.filter(mongo.db.manager.name.like(f'%{search_term}%')).all()  # Adjust based on your data model
    return render_template('admin/show_manager.html', managers=filtered_managers)



# Route for accepting a reservation
@main.route('/accept-reservation/<int:reservation_id>', methods=['POST'])  # Use int for the route
def accept_reservation(reservation_id):
    result = mongo.db.reservations.update_one(
        {'id_reservation': reservation_id},  # Use id_reservation as the key
        {'$set': {'statut': 'confirmé'}}  # Corrected field name
    )
    if result.modified_count:
        flash('Reservation has been confirmed.', 'success')
    else:
        flash('Failed to confirm the reservation or reservation not found.', 'error')
    return redirect(url_for('main.show_reservations'))

@main.route('/refuse-reservation/<int:reservation_id>', methods=['POST'])  # Use int for the route
def refuse_reservation(reservation_id):
    result = mongo.db.reservations.update_one(
        {'id_reservation': reservation_id},
        {'$set': {'statut': 'refusé'}}  # Corrected field name
    )
    if result.modified_count:
        flash('Reservation has been refused.', 'success')
    else:
        flash('Failed to refuse the reservation or reservation not found.', 'error')
    return redirect(url_for('main.show_reservations'))

@main.route('/generate-invoice/<int:reservation_id>')
def generate_invoice(reservation_id):
    # Fetch reservation details
    reservation = mongo.db['reservations'].find_one({'id_reservation': reservation_id})
    if not reservation:
        flash("Reservation not found.", "error")
        return redirect(url_for('main.dashboard'))

    # Fetch client and car details
    client = mongo.db['client'].find_one({'_id': ObjectId(reservation['id_client'])})
    car = mongo.db['car'].find_one({'_id': ObjectId(reservation['id_voiture'])})
    if not client or not car:
        flash("Details not found for the reservation.", "error")
        return redirect(url_for('main.dashboard'))

    # Date processing and price calculation
    start_date = datetime.strptime(reservation['dateDebut'], '%Y-%m-%d')
    end_date = datetime.strptime(reservation['dateFin'], '%Y-%m-%d')
    duration = (end_date - start_date).days
    daily_price = float(car.get('prix', 0))
    total_price = daily_price * duration

    # Initialize PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Facture", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(200, 10, "Voici les détails de la facture", 0, 1, 'C')
    pdf.cell(200, 10, "", 0, 1, 'C')

    # Calculate the starting x position to center the table (Assuming A4 width = 210mm)
    table_width = sum([50, 130])  # Sum of column widths
    start_x = (210 - table_width) / 2

    # Table headers with custom color #007bff (0, 123, 255)
    pdf.set_x(start_x)
    pdf.set_fill_color(0, 123, 255)  # Custom light blue background for headers
    pdf.set_font("Arial", 'B', 12)
    column_widths = [50, 130]  # Adjusted column widths
    headers = ["Données", "Détails"]
    for i, header in enumerate(headers):
        pdf.cell(column_widths[i], 10, header, 1, 0, 'C', 1)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", 'B', 12)  # Set data labels to bold
    fields = [
        ("ID de Réservation", str(reservation_id)),
        ("Client", f"{client['nom']} {client['prenom']}"),
        ("Voiture", f"{car['marque']} {car['modele']}"),
        ("Période de location", f"{reservation['dateDebut']} à {reservation['dateFin']}"),
        ("Durée de location", f"{duration} jours"),
        ("Prix par jour", f"${daily_price:.2f}"),
        ("Prix Total", f"${total_price:.2f}")
    ]
    for field, detail in fields:
        pdf.set_x(start_x)
        pdf.set_font("Arial", 'B', 12)  # Bold for field names
        pdf.cell(column_widths[0], 10, field, 1)
        pdf.set_font("Arial", '', 12)  # Regular for details
        pdf.cell(column_widths[1], 10, detail, 1)
        pdf.ln()

    # Footer text with current date and time
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, "", 0, 1, 'C')
    current_time = datetime.now().strftime("%d/%m/%Y, %H:%M")
    footer_text = f"Fait par CarQuest, le {current_time}"
    pdf.cell(0, 10, footer_text, 0, 1, 'C')  # Centered at bottom

    # Output the PDF to the browser
    pdf_response = pdf.output(dest='S').encode('latin1')
    response = Response(pdf_response, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{reservation_id}.pdf'
    return response