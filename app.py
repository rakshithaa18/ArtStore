import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from dotenv import load_dotenv
import random
import time
import random
from flask import session, flash, redirect, url_for
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask import send_file
import io
from datetime import datetime
from datetime import datetime, timedelta


# Load environment variables
load_dotenv()

app = Flask(__name__)  

from flask_mail import Mail, Message
import random

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rakshithashivarajaiah@gmail.com'   # your Gmail
app.config['MAIL_PASSWORD'] = 'wkps svik orje iouo'     # Gmail app password

mail = Mail(app)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.secret_key = os.getenv('SECRET_KEY', 'devkey')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = timedelta(days=7)


def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='RakshMahi@9876',   
        database='artstore'
    )
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT a.*, ar.name as artist_name FROM artworks a LEFT JOIN artists ar ON a.artist_id = ar.artist_id')
    artworks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', artworks=artworks)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = request.form['password']

        otp = random.randint(100000, 999999)

        session['otp'] = otp
        session['temp_user'] = {
            'username': username,
            'name': name,
            'phone_number': phone_number,
            'email': email,
            'password': password
        }

        msg = Message(
            subject="Artstore Email Verification OTP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Your OTP for Artstore registration is: {otp}"
        mail.send(msg)

        flash("OTP sent to your email", "info")
        return redirect(url_for('verify_motp'))

    return render_template('register.html')


@app.route('/verify-motp', methods=['GET', 'POST'])
def verify_motp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if int(entered_otp) == session.get('otp'):
            data = session.get('temp_user')

            hashed = generate_password_hash(data['password'])

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username,name, email,phone_number, password)
                VALUES (%s, %s, %s,%s,%s)
            """, (data['username'], data['name'], data['email'], data['phone_number'], hashed))
            conn.commit()
            cursor.close()
            conn.close()

            session.pop('otp')
            session.pop('temp_user')

            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))

        else:
            flash("Invalid OTP", "danger")

    return render_template('verify_motp.html')

@app.route('/motp-login', methods=['GET', 'POST'])
def motp_login():
    if request.method == 'POST':
        mmail = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, username FROM users WHERE email=%s",
            (mmail,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            flash("Email not registered", "danger")
            return redirect(url_for('motp_login'))

        otp = random.randint(100000, 999999)

        # ✅ Store OTP + user info
        session['otp'] = otp
        session['otp_user_id'] = user['user_id']
        session['otp_username'] = user['username']

        msg = Message(
            subject="Artstore Email Verification OTP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[mmail]
        )
        msg.body = f"Your OTP for Artstore login is: {otp}"
        mail.send(msg)

        flash("OTP sent to your email", "info")
        return redirect(url_for('verifyy_motp'))

    return render_template('motp_login.html')

@app.route('/verifyy-motp', methods=['GET', 'POST'])
def verifyy_motp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        # Validate OTP
        if int(entered_otp) == session.get('otp'):
            # ✅ Login user
            session['user_id'] = session.get('otp_user_id')
            session['username'] = session.get('otp_username')

            # ✅ Cleanup OTP session
            session.pop('otp', None)
            session.pop('otp_user_id', None)
            session.pop('otp_username', None)

            flash("Logged in successfully 🎉", "success")
            return redirect(url_for('index'))

        flash("Invalid OTP", "danger")

    return render_template('verify_otp.html')


    

@app.route('/otp-login', methods=['GET', 'POST'])
def otp_login():
    if request.method == 'POST':
        phone = request.form['phone_number']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id FROM users WHERE phone_number=%s",
            (phone,)
        )
        user = cursor.fetchone()

        if not user:
            flash("Phone number not registered", "danger")
            return redirect(url_for('otp_login'))

        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=5)

        cursor.execute("""
            UPDATE users
            SET otp=%s, otp_expiry=%s
            WHERE phone_number=%s
        """, (otp, expiry, phone))

        conn.commit()
        cursor.close()
        conn.close()

        # 🔔 For now (testing)
        print("OTP:", otp)

        session['otp_phone'] = phone
        flash("OTP sent successfully", "success")
        return redirect(url_for('verify_otp'))

    return render_template('otp_login.html')
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    phone = session.get('otp_phone')

    if not phone:
        return redirect(url_for('otp_login'))

    if request.method == 'POST':
        entered_otp = request.form['otp']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, otp, otp_expiry, username
            FROM users
            WHERE phone_number=%s
        """, (phone,))
        user = cursor.fetchone()

        if user and user['otp'] == entered_otp and user['otp_expiry'] > datetime.now():
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            cursor.execute("""
                UPDATE users SET otp=NULL, otp_expiry=NULL
                WHERE phone_number=%s
            """, (phone,))
            conn.commit()

            cursor.close()
            conn.close()

            flash("Logged in successfully 🎉", "success")
            return redirect(url_for('index'))

        flash("Invalid or expired OTP", "danger")

    return render_template('verify_otp.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['admin_id']
            session['admin_username'] = admin['username']
            flash('Admin logged in.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""SELECT 
        a.*,
        ar.name AS artist_name,
        ROUND(AVG(r.rating), 1) AS avg_rating,
        COUNT(r.review_id) AS review_count
    FROM artworks a
    LEFT JOIN artists ar ON a.artist_id = ar.artist_id
    LEFT JOIN reviews r ON a.artwork_id = r.artwork_id
    GROUP BY a.artwork_id
                   """ )
    artworks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', artworks=artworks)

@app.route('/admin/artwork/<int:artwork_id>/reviews')
def admin_view_reviews(artwork_id):
    if not session.get('admin_id'):
        flash("Admin login required", "danger")
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Artwork info
    cursor.execute("""
        SELECT title
        FROM artworks
        WHERE artwork_id = %s
    """, (artwork_id,))
    artwork = cursor.fetchone()

    # Reviews for this artwork
    cursor.execute("""
        SELECT 
            r.rating,
            r.comment,
            r.created_at,
            u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.artwork_id = %s
        ORDER BY r.created_at DESC
    """, (artwork_id,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_artwork_reviews.html',
        artwork=artwork,
        reviews=reviews
    )


@app.route('/admin/add', methods=['GET', 'POST'])
def add_artwork():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM artists')
    artists = cursor.fetchall()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        artist_id = request.form.get('artist_id') or None
        qty = request.form.get('qty', 1)
        file = request.files.get('image')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cursor.execute('INSERT INTO artworks (title, description, price, image_filename, artist_id, available_qty) VALUES (%s,%s,%s,%s,%s,%s)',
                       (title, description, price, filename, artist_id, qty))
        conn.commit()
        flash('Artwork added!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    cursor.close()
    conn.close()
    return render_template('add_artwork.html', artists=artists)


@app.route('/artwork/<int:artwork_id>')
def artwork_detail(artwork_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Fetch artwork details
    cursor.execute("""
        SELECT a.*, ar.name AS artist_name
        FROM artworks a
        LEFT JOIN artists ar ON a.artist_id = ar.artist_id
        WHERE a.artwork_id = %s
    """, (artwork_id,))
    art = cursor.fetchone()

    if not art:
        cursor.close()
        conn.close()
        flash('Artwork not found', 'warning')
        return redirect(url_for('index'))

    # 2️⃣ Fetch average rating + count
    cursor.execute("""
        SELECT AVG(rating) AS avg_rating, COUNT(*) AS total_reviews
        FROM reviews
        WHERE artwork_id = %s
    """, (artwork_id,))
    rating_info = cursor.fetchone()

    # 3️⃣ Fetch individual reviews
    cursor.execute("""
        SELECT r.rating, r.comment, r.created_at, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.artwork_id = %s
        ORDER BY r.created_at DESC
    """, (artwork_id,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    # 4️⃣ Send everything to template
    return render_template(
        'artwork_detail.html',
        art=art,
        rating_info=rating_info,
        reviews=reviews
    )


@app.route('/add_to_cart/<int:artwork_id>', methods=['POST'])
def add_to_cart(artwork_id):
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(artwork_id)] = cart.get(str(artwork_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0

    if cart:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        format_ids = ','.join(['%s'] * len(cart.keys()))
        cursor.execute(
            f'SELECT * FROM artworks WHERE artwork_id IN ({format_ids})',
            tuple(cart.keys())
        )
        rows = cursor.fetchall()

        for r in rows:
            aid = str(r['artwork_id'])
            qty = cart.get(aid, 0)
            subtotal = qty * float(r['price'])
            total += subtotal

            items.append({
                'art': r,
                'qty': qty,
                'subtotal': subtotal
            })

        cursor.close()
        conn.close()

    # 🔥 Discount Preview
    discount_percentage = 0
    if total >= 10000:
        discount_percentage = 15
    elif total >= 5000:
        discount_percentage = 10

    discount_amount = (total * discount_percentage) / 100
    total_after_discount = total - discount_amount

    return render_template(
        'cart.html',
        items=items,
        total=total,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        total_after_discount=total_after_discount
    )


@app.route('/checkout_page')
def checkout_page():
    if 'user_id' not in session:
        flash('Please login to continue checkout.', 'warning')
        return redirect(url_for('login'))
    return render_template('checkout.html')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        address = request.form.get('address')
        delivery_date = request.form.get('delivery_date')
        payment_mode = request.form.get('payment_mode')

        if not address or not delivery_date or not payment_mode:
            flash('Please fill all fields before submitting.', 'danger')
            return redirect(url_for('checkout'))

        cart = session.get('cart', {})
        if not cart:
            flash('Cart is empty.', 'warning')
            return redirect(url_for('index'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        
        ids = tuple(cart.keys())
        format_ids = ','.join(['%s'] * len(ids))
        cursor.execute(f'SELECT * FROM artworks WHERE artwork_id IN ({format_ids})', ids)
        rows = cursor.fetchall()

        
        total = sum(float(r['price']) * cart[str(r['artwork_id'])] for r in rows)

        
        discount_percentage = 0
        if total >= 10000:
            discount_percentage = 15
        elif total >= 5000:
            discount_percentage = 10

        discount_amount = total * discount_percentage / 100
        total_after_discount = total - discount_amount


    
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, total_amount,discount,total_after_discount, address, delivery_date, payment_mode)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (session['user_id'], total,discount_amount,total_after_discount, address, delivery_date, payment_mode))
        order_id = cursor.lastrowid
        

        
        for r in rows:
            qty = cart[str(r['artwork_id'])]
            cursor.execute('''
                INSERT INTO order_items (order_id, artwork_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, r['artwork_id'], qty, float(r['price'])))
            cursor.execute('UPDATE artworks SET status = %s WHERE artwork_id = %s', ('Sold', r['artwork_id']))
            cursor.execute('''
                UPDATE artworks
                SET available_qty = available_qty - %s
                WHERE artwork_id = %s
            ''', (qty, r['artwork_id']))



        conn.commit()
        cursor.close()
        conn.close()

        session.pop('cart', None)
        
        if discount_percentage > 0:
            message = f"🎉 Congrats! You got a {discount_percentage}% discount."
        else:
            message = "✅ Order placed successfully!"

        return render_template(
            'order_success.html',
            message=message,
            total=total_after_discount,
            order_id=order_id
        )
  
    return render_template('checkout.html')



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin/delete_artwork/<int:artwork_id>', methods=['POST'])
def delete_artwork(artwork_id):
    if 'admin_id' not in session:
        flash('Access denied! Admin login required.', 'danger')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM artworks WHERE artwork_id = %s', (artwork_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Artwork deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/update_quantity/<int:artwork_id>', methods=['POST'])
def update_quantity(artwork_id):
    if 'admin_id' not in session:
        flash('Access denied! Admin login required.', 'danger')
        return redirect(url_for('admin_login'))

    new_qty = request.form.get('new_qty')

    if not new_qty or not new_qty.isdigit():
        flash('Invalid quantity input.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_qty = int(new_qty)
    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute('UPDATE artworks SET available_qty = %s WHERE artwork_id = %s', (new_qty, artwork_id))

    
    if new_qty > 0:
        cursor.execute("UPDATE artworks SET status = 'Available' WHERE artwork_id = %s", (artwork_id,))
    else:
        cursor.execute("UPDATE artworks SET status = 'Sold' WHERE artwork_id = %s", (artwork_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Artwork quantity updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/analytics')
def analytics():
    
    if 'user_id' not in session and 'admin_id' not in session:
        flash("Please login to view analytics.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

   
    cursor.execute("""
        SELECT 
            CASE 
                WHEN price < 1000 THEN 'Below ₹1000'
                WHEN price BETWEEN 1000 AND 5000 THEN '₹1000 - ₹5000'
                WHEN price BETWEEN 5000 AND 10000 THEN '₹5000 - ₹10000'
                ELSE 'Above ₹10000'
            END AS price_range,
            COUNT(*) AS count
        FROM artworks
        GROUP BY price_range
    """)
    price_data = cursor.fetchall()

    
    cursor.execute("SELECT title, price FROM artworks ORDER BY price DESC LIMIT 5")
    expensive_artworks = cursor.fetchall()

    
    cursor.execute("""
        SELECT title, price, image_filename 
        FROM artworks 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    recent_artworks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'analytics.html',
        price_data=price_data,
        expensive_artworks=expensive_artworks,
        recent_artworks=recent_artworks
    )

@app.route('/update_cart/<int:artwork_id>/<string:action>')
def update_cart(artwork_id, action):
    cart = session.get('cart', {})
    artwork_id = str(artwork_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT available_qty FROM artworks WHERE artwork_id = %s",
        (artwork_id,)
    )
    art = cursor.fetchone()

    cursor.close()
    conn.close()

    if not art:
        flash("Artwork not found", "danger")
        return redirect(url_for('cart'))

    available_qty = art['available_qty']
    current_qty = cart.get(artwork_id, 0)

    if action == 'increase':
        if current_qty < available_qty:
            cart[artwork_id] = current_qty + 1
        else:
            flash("⚠ Cannot exceed available stock", "warning")

    elif action == 'decrease':
        if current_qty > 1:
            cart[artwork_id] = current_qty - 1
        else:
            cart.pop(artwork_id, None)

    elif action == 'remove':
        cart.pop(artwork_id, None)

    session['cart'] = cart
    return redirect(url_for('cart'))



@app.route('/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        flash('Please login to search artworks.', 'warning')
        return redirect(url_for('login'))

    query = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    
    cursor.execute("SHOW COLUMNS FROM artworks")
    columns = [col['Field'] for col in cursor.fetchall()]

    sql = "SELECT * FROM artworks"
    params = ()

    if query:
        conditions = []
        if 'title' in columns:
            conditions.append("title LIKE %s")
        if 'artist_name' in columns:
            conditions.append("artist_name LIKE %s")
        if 'artist' in columns:
            conditions.append("artist LIKE %s")
        if 'description' in columns:
            conditions.append("description LIKE %s")

        if conditions:
            sql += " WHERE " + " OR ".join(conditions)
            params = tuple([f"%{query}%"] * len(conditions))

    cursor.execute(sql, params)
    artworks = cursor.fetchall()

    cursor.close()
    conn.close()

    
    if not artworks:
        flash(f'No results found for "{query}". Please try another search.', 'info')
        return render_template('index.html', artworks=[], query=query, no_results=True)

   
    return render_template('index.html', artworks=artworks, query=query, no_results=False)

from datetime import date

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please login to view profile", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- USER INFO ----------------
    cursor.execute("""
        SELECT username, email, name, phone_number
        FROM users 
        WHERE user_id = %s
    """, (session['user_id'],))
    user = cursor.fetchone()

    # ---------------- ORDERS ----------------
    cursor.execute("""
        SELECT 
            order_id,
            address,
            total_amount,
            discount,
            (total_amount - discount) AS total_after_discount,
            status,
            delivery_date,
            delivered_at,
            cancelled_at,
            created_at,
            returned_at
        FROM orders
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session['user_id'],))
    orders = cursor.fetchall()

    RETURN_DAYS_LIMIT = 7

    # ---------------- ORDER ITEMS + REVIEWS ----------------
    for order in orders:

        # ---- Items ----
        cursor.execute("""
            SELECT 
                oi.quantity,
                oi.unit_price,
                a.title,
                a.image_filename,
                a.artwork_id
            FROM order_items oi
            JOIN artworks a ON oi.artwork_id = a.artwork_id
            WHERE oi.order_id = %s
        """, (order['order_id'],))
        items = cursor.fetchall()

        final_items = []

        for item in items:
            # 🔥 STEP 3: CHECK IF REVIEW EXISTS
            cursor.execute("""
                SELECT 1 FROM reviews
                WHERE user_id = %s AND artwork_id = %s AND order_id = %s
            """, (
                session['user_id'],
                item['artwork_id'],
                order['order_id']
            ))

            reviewed = cursor.fetchone() is not None

            final_items.append({
                "artwork_id": item['artwork_id'],
                "title": item['title'],
                "quantity": item['quantity'],
                "unit_price": item['unit_price'],
                "image_url": url_for(
                    'static',
                    filename='uploads/' + (item['image_filename'] or 'placeholder.png')
                ),
                "reviewed": reviewed   # ✅ KEY FIX
            })

        order['items'] = final_items

        # ---- Return eligibility ----
        order['return_allowed'] = False

        if order['status'] == 'Completed' and order['delivered_at']:
            delivered_at = order['delivered_at']
            delivered_date = (
                delivered_at.date()
                if isinstance(delivered_at, datetime)
                else delivered_at
            )

            if date.today() <= delivered_date + timedelta(days=RETURN_DAYS_LIMIT):
                order['return_allowed'] = True

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        user=user,
        orders=orders
    )


def generate_invoice_pdf(order, items):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Logo (optional – put your logo in static/images/logo.png)
    try:
        pdf.drawImage("static/images/logo.png", 50, y-40, width=80, height=40)
    except:
        pass

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(150, y, "ARTSTORE INVOICE")
    y -= 50

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Invoice ID: #{order['order_id']}")
    y -= 15
    pdf.drawString(50, y, f"Order Date: {order['created_at']}")
    y -= 15

    if order['delivered_at']:
        pdf.drawString(50, y, f"Delivered On: {order['delivered_at']}")
        y -= 15
    if order['returned_at']:
        pdf.drawString(50,y, f"Returned on:  {order['returned_at']}")
        y -= 15
    if order['cancelled_at']:
        pdf.drawString(50,y, f"Cancelled on:  {order['cancelled_at']}")
        y -=15
    pdf.drawString(50, y, f"Customer: {order['username']}")
    y -= 15
    pdf.drawString(50, y, f"Email: {order['email']}")
    y -= 25

    # Items header
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Items")
    y -= 20

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Artwork")
    pdf.drawString(280, y, "Qty")
    pdf.drawString(330, y, "Price")
    pdf.drawString(400, y, "Total")
    y -= 15

    pdf.setFont("Helvetica", 10)
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        pdf.drawString(50, y, item['title'])
        pdf.drawString(280, y, str(item['quantity']))
        pdf.drawString(330, y, f"Rs {item['unit_price']}")
        pdf.drawString(400, y, f"Rs {line_total}")
        y -= 15

    y -= 20

    # Pricing
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, f"Subtotal: Rs. {order['total_amount']}")
    y -= 15
    pdf.drawString(50, y, f"Discount: -Rs. {order['discount']}")
    y -= 15
    pdf.drawString(50, y, f"GST (18%): Rs. {order['gst']}")
    y -= 15
    pdf.drawString(50, y, f"Final Amount Paid: Rs. {order['total_after_discount']}")

    y -= 30
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(50, y, "Thank you for shopping with Artstore")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

@app.route('/invoice/<int:order_id>')
def download_invoice(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT o.*, u.username, u.email
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE o.order_id=%s AND o.user_id=%s
    """, (order_id, session['user_id']))
    order = cursor.fetchone()

    cursor.execute("""
        SELECT a.title, oi.quantity, oi.unit_price
        FROM order_items oi
        JOIN artworks a ON oi.artwork_id = a.artwork_id
        WHERE oi.order_id=%s
    """, (order_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    pdf_buffer = generate_invoice_pdf(order, items)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"invoice_{order_id}.pdf",
        mimetype="application/pdf"
    )

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone_number')

        cursor.execute("""
            UPDATE users
            SET  name = %s, phone_number = %s
            WHERE user_id = %s
        """, ( name, phone, session['user_id']))

        conn.commit()
        flash("Profile updated successfully ✅", "success")
        cursor.close()
        conn.close()
        return redirect(url_for('profile'))

    # GET → load current user data
    cursor.execute("""
        SELECT username, name, phone_number, email
        FROM users
        WHERE user_id = %s
    """, (session['user_id'],))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('edit_profile.html', user=user)



@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current = request.form['current_password']
        new = request.form['new_password']
        confirm = request.form['confirm_password']

        if new != confirm:
            flash("New passwords do not match", "danger")
            return redirect(url_for('change_password'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT password FROM users WHERE user_id=%s",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if not check_password_hash(user['password'], current):
            flash("Current password is incorrect", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('change_password'))

        hashed = generate_password_hash(new)
        cursor.execute(
            "UPDATE users SET password=%s WHERE user_id=%s",
            (hashed, session['user_id'])
        )
        conn.commit()

        cursor.close()
        conn.close()

        flash("Password changed successfully ✅", "success")
        return redirect(url_for('profile'))

    # GET request → show page
    return render_template('change_password.html')


@app.route('/admin/manage')
def admin_manage():
    if not session.get('admin_id'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS count FROM users")
    total_users = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM orders")
    total_orders = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM artworks")
    total_artworks = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template('admin_manage.html',
                           total_users=total_users,
                           total_orders=total_orders,
                           total_artworks=total_artworks,
                           current_year=datetime.now().year)



@app.route('/admin/manage/users')
def admin_manage_users():
    if not session.get('admin_id'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()  
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    user_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_users.html', users=user_data)


@app.route('/admin/manage/orders')
def admin_manage_orders():
    if not session.get('admin_id'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()  
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.order_id, u.username, o.total_amount, o.discount, o.total_after_discount, o.status, o.created_at, o.delivered_at, r.rating, r.comment
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        LEFT JOIN reviews r ON o.order_id = r.order_id
    """)
    order = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_orders.html', orders=order)


@app.route('/mark_delivered/<int:order_id>')
def mark_delivered(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    delivered_at = datetime.now()

    cursor.execute("""
        UPDATE orders
        SET status='Completed', delivered_at=%s
        WHERE order_id=%s
    """, (delivered_at, order_id))
    conn.commit()

    # Fetch order + user
    cursor.execute("""
        SELECT o.*, u.email, u.username
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE o.order_id=%s
    """, (order_id,))
    order = cursor.fetchone()

    cursor.execute("""
        SELECT a.title, oi.quantity, oi.unit_price
        FROM order_items oi
        JOIN artworks a ON oi.artwork_id = a.artwork_id
        WHERE oi.order_id=%s
    """, (order_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    # Generate invoice
    pdf_buffer = generate_invoice_pdf(order, items)

    # Email invoice
    msg = Message(
        subject="Your Artstore Invoice",
        sender=app.config['MAIL_USERNAME'],
        recipients=[order['email']]
    )
    msg.body = f"""
Hi {order['username']},

Your order #{order_id} has been delivered successfully 🎉
Please find your invoice attached.

Thank you,
Artstore Team
"""
    msg.attach(
        filename=f"invoice_{order_id}.pdf",
        content_type="application/pdf",
        data=pdf_buffer.read()
    )

    mail.send(msg)

    flash("Order marked as delivered & invoice emailed", "success")
    return redirect(url_for('admin_manage_orders'))
 

@app.route('/cancel_order/<int:order_id>')
def cancel_order(order_id):
    if 'user_id' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check order status
    cursor.execute("""
        SELECT status FROM orders
        WHERE order_id = %s AND user_id = %s
    """, (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        flash("Order not found", "danger")
    elif order['status'] == 'Completed':
        flash("Delivered orders cannot be cancelled", "danger")
    elif order['status'] =='Returned':
        flash("Returned orders cannot be cancelled", "danger")
    else:
        cursor.execute("""
            UPDATE orders
            SET status = 'Cancelled',
                cancelled_at = %s
            WHERE order_id = %s
        """, (date.today(), order_id))
        conn.commit()
        flash("Order cancelled successfully", "success")

    cursor.close()
    conn.close()
    return redirect(url_for('profile'))

@app.route('/return_order/<int:order_id>')
def return_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = 'Return Requested'
        WHERE order_id = %s
          AND user_id = %s
          AND status = 'Completed'
    """, (order_id, session['user_id']))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Return request submitted. Awaiting admin approval ⏳", "info")
    return redirect(url_for('profile'))

@app.route('/approve_return/<int:order_id>')
def approve_return(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = 'Returned',
            returned_at = NOW()
        WHERE order_id = %s
          AND status = 'Return Requested'
    """, (order_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Return approved successfully ✅", "success")
    return redirect(url_for('admin_manage_orders'))

@app.route('/cancel_request/<int:order_id>')
def cancel_request(order_id):
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute(""" UPDATE orders
                   SET status='Completed'
                   WHERE order_id = %s
                   """,(order_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Return request cancelled", "success")
    return redirect(url_for('profile'))

@app.route('/add_review/<int:artwork_id>/<int:order_id>', methods=['POST'])
def add_review(artwork_id, order_id):
    if 'user_id' not in session:
        flash("Please login to submit a review.", "warning")
        return redirect(url_for('login'))

    rating = request.form.get('rating')
    comment = request.form.get('comment')

    if not rating or not comment:
        flash("Rating and comment are required.", "danger")
        return redirect(url_for('profile'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO reviews (user_id, artwork_id, order_id, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            artwork_id,
            order_id,
            rating,
            comment
        ))

        conn.commit()
        flash("✅ Review submitted successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash("⚠ You already reviewed this artwork.", "warning")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('profile'))


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
