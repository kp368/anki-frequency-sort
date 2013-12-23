# import the main window object (mw) from ankiqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
# import libraries to scrape Google results
import requests, re


# Sort note ids by frequency of their occurrence on the internet
def sort_by_freq(nids):
    
    # Google search for the word and scrape the number of results
    def get_freq(nid):
        
        note = mw.col.getNote(nid)
        field = note.fields[1] # Get second field, which corresponds to the Italian word
        
        # Get search results
        status = None
        tries = 0
        while status != 200 and tries < 3:
            search_results = requests.get("https://www.google.co.uk/search", params={'q':field})
            status = search_results.status_code
            tries += 1
            
        if status != 200:
            print "Failed to look up " + field
        
        # Scrape result count 
        search_count = re.search(r'About ([0-9,]*) results', search_results.content)
        if search_count:
            count = int(search_count.groups()[0].replace(',',''))
        else:
            print "Didn't find result for " + field + ", assuming 0."
            count = 0
        
        return count

    
    nids = sorted(nids, key=get_freq, reverse=True)
    
    return nids

def order_by_freq():
    # Get current deck
    did = mw.col.decks.selected()
    # Get all notes in current deck
    nids_dup = mw.col.db.list("select nid from cards where type=0 and did=?", did)
    
    # Deduplicate note ids
    nids = []
    nidsSet = set()
    for nid in nids_dup:
        if nid not in nidsSet:
            nids.append(nid)
            nidsSet.add(nid)
            
    if not nids:
        # No new cards
        return
        
    nids = sort_by_freq(nids)

    # Determine nid ordering
    due = {}
    for c, nid in enumerate(nids):
        due[nid] = 1 + c

    # Save new card order
    d = []
    for id, nid in mw.col.db.execute(
        "select id, nid from cards where type = 0 and did=?", did):
        d.append(dict(due=due[nid], usn=mw.col.usn(), cid=id))
    mw.col.db.executemany(
        "update cards set due=:due,usn=:usn where id = :cid", d)
    

# Create a new menu item, "Order by Frequency"
action = QAction("Order by Frequency", mw)
# Set it to call order_by_freq when it's clicked
mw.connect(action, SIGNAL("triggered()"), order_by_freq)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
