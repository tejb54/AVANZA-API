from avanza import Avanza

def main():
  avanza = Avanza()
  accounts = avanza.get_accounts()
  print(accounts)

  
if __name__ == "__main__":
  main()