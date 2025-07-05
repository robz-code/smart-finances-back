from app.config.database import Base, engine
import app.entities.user  # Import all your models so Base.metadata knows about them
import app.entities.user_contact
import app.entities.account
import app.entities.credit
import app.entities.category
import app.entities.transaction
import app.entities.installment
import app.entities.recurring_transaction
import app.entities.recurring_debt
import app.entities.user_debt
import app.entities.group
import app.entities.group_member
import app.entities.budget
import app.entities.budget_category

def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    create_all_tables()
