import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
tr=load('trainers.json')
KNOWN=['Roxanne','Brawly','Wattson','Flannery','Norman','Winona','Tate','Liza','Juan','Sidney','Phoebe','Glacia','Drake','Wallace','Steven',
 'May','Brendan','Wally','Roark','Gardenia','Maylene','Wake','Fantina','Byron','Candice','Volkner','Aaron','Bertha','Flint','Lucian','Cynthia','Volo',
 'Red','Leon','Ash','Serena','Archie','Maxie','Matt','Shelly','Tabitha','Courtney','Zinnia','Blue','Green','Gary','Lance','Giovanni','Cyrus','Ghetsis','N','Lysandre','Guzma','Lusamine','Faba','Gladion','Hop','Bede','Marnie','Rose','Oleana','Sonia','Kukui','Lillie','Hau','Dawn','Lucas','Barry','Cheren','Bianca','Hilbert','Hilda','Nate','Rosa','Hugh','Calem','Shauna','Elio','Selene','Gloria','Victor','Wes','Rui','Brock','Misty','Surge','Erika','Koga','Sabrina','Blaine','Falkner','Bugsy','Whitney','Morty','Chuck','Jasmine','Pryce','Clair','Will','Karen','Bruno','Lorelei','Agatha','Cilan','Chili','Cress','Lenora','Burgh','Elesa','Clay','Skyla','Brycen','Drayden','Iris','Roxie','Marlon','Shauntal','Grimsley','Caitlin','Marshal','Alder','Viola','Grant','Korrina','Ramos','Clemont','Valerie','Olympia','Wulfric','Malva','Siebold','Wikstrom','Drasna','Diantha','Hala','Olivia','Nanu','Hapu','Molayne','Acerola','Kahili','Milo','Nessa','Kabu','Bea','Allister','Opal','Gordie','Melony','Piers','Raihan','Mustard','Peony','Kieran','Carmine','Nemona','Penny','Arven','Geeta','Larry','Rika','Poppy','Hassel','Katy','Brassius','Iono','Kofu','Tulip','Grusha','Ryme','Eri','Giacomo','Mela','Atticus','Ortega','Adaman','Irida','Kamado','Ingo','Emmet','Anabel','Tucker','Spenser','Greta','Noland','Lucy','Brandon','Mr. Briney','Scott','Riley','Cheryl','Mira','Buck','Marley','Looker','Saturn','Mars','Jupiter','Charon','Colress','Zinzolin','Xerosic','Plumeria','Sina','Dexio','Wattson','Yanshan','Palmer','Thorton','Dahlia','Darach','Argenta','Caitlin','Morimoto','Cook','Gold','Silver','Kris','Lyra','Ethan','Chase','Elaine','Trace','Leaf','Ariana','Archer','Petrel','Proton','Jessie','James','Nemona','Wataru','Erika']
CLASS_KEY={'Leader','Elite Four','Champion','Aqua Leader','Magma Leader','Aqua Admin','Magma Admin','Salon Maiden','Dome Ace','Palace Maven','Arena Tycoon','Factory Head','Pike Queen','Pyramid King','Lorekeeper'}
def match(t):
    if t['class'] in CLASS_KEY: return True
    n=t['name']
    if n in KNOWN: return True
    if t['class']=='PkMn Trainer' and n and n not in ('Grunt',): return True
    return False
sel=[t for t in tr if not t.get('invalid') and match(t) and t['party_size']>0]
# group by name
groups={}
for t in sel: groups.setdefault(t['name'],[]).append(t)
order=['Roxanne','Brawly','Wattson','Flannery','Norman','Winona','Tate&Liza','Tate','Liza','Juan','Sidney','Phoebe','Glacia','Drake','Wallace','May','Brendan','Wally','Roark','Gardenia','Maylene','Wake','Crasher Wake','Fantina','Byron','Candice','Volkner','Aaron','Bertha','Flint','Lucian','Cynthia','Volo','Steven','Red','Leon','Ash','Serena','Archie','Maxie']
names=[n for n in order if n in groups]+sorted(n for n in groups if n not in order and '{CN' not in n)+sorted(n for n in groups if '{CN' in n)
with open(os.path.join(OUT,'key_trainers.md'),'w',encoding='utf-8') as f:
    f.write('# Key trainers (Hyper Emerald v5.7) — every version of each name\n\n')
    f.write('Source: gTrainers @ ROM 0x090019F8 (902 entries, 40 bytes each). Class names @ 0x0830FCD4. Party entries: {u16 iv, u16 level, u16 species, [u16 item], [u16 moves x4]} (vanilla partyFlags rules).\n')
    f.write('Selection: class Leader / Elite Four / Champion / Aqua+Magma Leader+Admin / Frontier Brains / Lorekeeper, every "PkMn Trainer"-class trainer with a name, plus a list of known character names.\n\n')
    for n in names:
        f.write('## %s\n\n'%n)
        for t in groups[n]:
            lv=[m['level'] for m in t['party']]
            f.write('### #%d  %s %s  — %d Pokémon, Lv %d–%d%s%s\n\n'%(t['id'],t['class'],t['name'],t['party_size'],min(lv),max(lv),' (DOUBLE)' if t['double'] else '',' — items: '+', '.join(t['items']) if t['items'] else ''))
            f.write('| # | Pokémon | Lv | Held item | Moves |\n|---|---|---|---|---|\n')
            for i,m in enumerate(t['party'],1):
                f.write('| %d | %s (#%d) | %d | %s | %s |\n'%(i,m['species'],m['species_id'],m['level'],m['item'] or '—',', '.join(x for x in m['moves'] if x) or '—'))
            f.write('\n')
print('key trainers:', len(sel), 'names', len(names))
print(names)
