-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  phone_number TEXT,
  is_registered BOOLEAN DEFAULT FALSE,
  currency TEXT,
  language TEXT,
  profile_image TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User Contacts
CREATE TABLE user_contacts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  contact_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Accounts
CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  currency TEXT,
  initial_balance NUMERIC DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_deleted BOOLEAN DEFAULT FALSE
);

-- Credits
CREATE TABLE credits (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts(id) UNIQUE,
  type TEXT NOT NULL,
  limit NUMERIC,
  cutoff_day INT,
  payment_due_day INT,
  interest_rate NUMERIC,
  term_months INT,
  start_date DATE,
  end_date DATE,
  grace_days INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_deleted BOOLEAN DEFAULT FALSE
);

-- Categories
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT,
  color TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  account_id UUID REFERENCES accounts(id),
  category_id UUID REFERENCES categories(id),
  group_id UUID REFERENCES groups(id),
  recurrent_transaction_id UUID REFERENCES recurring_transactions(id),
  transfer_id UUID REFERENCES transactions(id),
  type TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  currency TEXT,
  date DATE NOT NULL,
  note TEXT,
  source TEXT DEFAULT 'manual',
  has_installments BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Installments
CREATE TABLE installments (
  id UUID PRIMARY KEY,
  transaction_id UUID REFERENCES transactions(id),
  installment_number INT,
  amount NUMERIC NOT NULL
);

-- Recurring Transactions
CREATE TABLE recurring_transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  account_id UUID REFERENCES accounts(id),
  category_id UUID REFERENCES categories(id),
  group_id UUID REFERENCES groups(id),
  type TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  start_date DATE NOT NULL,
  rrule TEXT NOT NULL,
  note TEXT,
  source TEXT DEFAULT 'manual',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Recurring Debt
CREATE TABLE recurring_debt (
  id UUID PRIMARY KEY,
  recurring_transaction_id UUID REFERENCES recurring_transactions(id),
  from_user_id UUID REFERENCES users(id),
  to_user_id UUID REFERENCES users(id),
  amount NUMERIC NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User Debts
CREATE TABLE user_debts (
  id UUID PRIMARY KEY,
  transaction_id UUID REFERENCES transactions(id),
  from_user_id UUID REFERENCES users(id),
  to_user_id UUID REFERENCES users(id),
  amount NUMERIC NOT NULL,
  type TEXT NOT NULL,
  note TEXT,
  date TIMESTAMP DEFAULT NOW()
);

-- Groups
CREATE TABLE groups (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Group Members
CREATE TABLE group_members (
  id UUID PRIMARY KEY,
  group_id UUID REFERENCES groups(id),
  user_id UUID REFERENCES users(id),
  joined_at TIMESTAMP DEFAULT NOW()
);

-- Budgets
CREATE TABLE budgets (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  account_id UUID REFERENCES accounts(id),
  name TEXT NOT NULL,
  recurrence TEXT NOT NULL,
  start_date DATE,
  end_date DATE,
  amount NUMERIC NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Budget Categories
CREATE TABLE budget_categories (
  budget_id UUID REFERENCES budgets(id),
  category_id UUID REFERENCES categories(id),
  PRIMARY KEY (budget_id, category_id)
);
