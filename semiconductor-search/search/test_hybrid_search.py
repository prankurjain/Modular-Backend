from search.hybrid_search import find_alternatives

result = find_alternatives("TIP120")

print("\nBASE PRODUCT:")
print(result["base_product"])

print("\nALTERNATIVES:\n")

for alt in result["alternatives"]:
    print(alt)