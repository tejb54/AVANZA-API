from avanza import Avanza

def main():
  avanza = Avanza()
  #print(avanza.get_accounts())
  #print('--------------------------')
  print(avanza.get_accounts_total_value())
  #print('--------------------------')
  #print(avanza.get_holdings_csv_file())
  #aktie_total, fond_total = get_total_by_type(avanza.get_holdings_csv_file())
  #print('Fond total: {}'.format(fond_total))
  #print('Aktie total: {}'.format(aktie_total))
  #print('--------------------------')
  #print(avanza.get_total_summary_csv())

def get_total_by_type(csv_string): ##Parse the csv string to get the totals
  fond_total = 0
  aktie_total = 0
  for row in csv_string.split('\n'):
    if row == '':
      continue
    row_split = row.split(';')
    if row_split[7] == 'Fond':
      fond_total += float(row_split[3])
    if row_split[7] == 'Aktie':
      aktie_total += float(row_split[3])
  return aktie_total, fond_total

if __name__ == "__main__":
  main()