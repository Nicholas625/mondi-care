from database import db 
 
print("Testing database...") 
 
officers = db.get_all_officers() 
print(f"\n Found {len(officers)} officers:") 
for officer in officers: 
    print(f"   - {officer['name']} ({officer['district']})") 
 
shops = db.get_all_shops() 
print(f"\n Found {len(shops)} shops:") 
for shop in shops: 
    print(f"   - {shop['name']} ({shop['type']})") 
 
print("\n Database is working!") 
