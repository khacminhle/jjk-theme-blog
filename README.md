<h1>Blog Website - Full Web Application</h1>
<h2>Tech Stack: Flask, Jinja Template, Bootstrap, Postgresql</h2>
<h3>App Demo Link: </h3>

<h3>Features: </h3>
<p>CRUD capabilities to create, read, update and delete blog articles. </p>

<h3>Application idea: </h3>
<p> JJK (Jujutsy Kaizen - Socecrey fight) is my favourite anime of all time. 
  Because of that I want to create a blog application that houses all of my favourite 
  characters and informaation about them. THe web application also has a comment section 
  for each blog post.
</p>

<h3>Code High Light</h3>

<h4> Admin decocator </h4>

```
def admin_required(func):
    @wraps(func)
    def wrapper_function(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            return abort(403)
    
    
    return wrapper_function
```

<p>
  This is a wrapper function that checks if the current user has id=1, indicating admin user.
  If it is, the application will grant them access to create features. 
</p>

```
@app.route("/new-post", methods=["GET", "POST"])
@admin_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)
```

<p>Implementation of admin wrapper function on the 'create' view</p>

<h4>Database Schema</h4>

```
class User(db.Model, UserMixin): 
    __tablename__ = 'user_db'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")
```

<p>
Database schema for user, each user will have name, email address, passwords 
posts associated with it. 
</p>

<h4>Front End Code</h4>

```
{% for post in all_posts %}
      <div class="post-preview bd-highlight" >
       
        <a href="{{ url_for('show_post', post_id=post.id) }}" class="text-light text-decoration-none">
          <img src="{{ post.img_url }}" class="img-fluid img-thumbnail rounded">
          <p class="post-title">{{ post.title }}</p>
          <p class="post-subtitle text-light">{{ post.subtitle[:60] }}...</p>
        </a>
       
        <div class="post-meta row justify-content-end ">
          <p class="post-meta">
            <a href="#">{{ post.author.name }}</a>
            on {{post.date}}
            <!-- TODO: Only show delete button if user id is 1 (admin user) -->
            {% if current_user.get_id() == '1' %}
            <a href="{{url_for('delete_post', post_id=post.id) }}">✘</a>
            {% endif %}
          </p>
        </div>
        
      </div>
      <!-- Divider-->
      <hr class="my-4" />
      {% endfor %}
```

<p>Snippet of front end code using HTML and Bootstrap to organise components</p>


