import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=ROOT/"noethys"
SOURCE_PATH=SOURCE_ROOT/"GestionDB.py"

def load_func(interface):
 source=SOURCE_PATH.read_text(encoding="utf-8"); tree=ast.parse(source)
 funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="GetConnexionReseau"]
 if len(funcs)!=1: raise AssertionError(funcs)
 module=ast.Module(body=funcs,type_ignores=[]); ast.fix_missing_locations(module)
 class C:
  def set_character_set(self,v): self.charset=v
 class MDB:
  @staticmethod
  def connect(**kw): c=C(); c.kwargs=kw; return c
 class Conn:
  @staticmethod
  def connect(**kw): c=C(); c.kwargs=kw; return c
 class Mysql: connector=Conn()
 class FT: LONG="LONG"
 ns={"INTERFACE_MYSQL":interface,"POOL_MYSQL":0,"CERTIFICATS_SSL":{},"MySQLdb":MDB(),"mysql":Mysql(),"FIELD_TYPE":FT,"conversions":{},"DecodeMdpReseau":lambda v:v}
 exec(compile(module,str(SOURCE_PATH),"exec"),ns); return ns["GetConnexionReseau"]

class T(unittest.TestCase):
 F="3306;localhost;user;password[RESEAU]Base_DATA.dat"
 def test_mysqldb(self):
  c,n=load_func("mysqldb")(self.F); self.assertEqual(c.charset,"utf8"); self.assertEqual(c.kwargs["host"],"localhost"); self.assertEqual(n,"base_data.dat")
 def test_connector(self):
  c,n=load_func("mysql.connector")(self.F); self.assertEqual(c.kwargs["port"],3306); self.assertEqual(n,"base_data.dat")
 def test_unknown(self):
  with self.assertRaisesRegex(ValueError,"Interface MySQL non supportée"): load_func("unexpected")(self.F)
 def test_gap_gone(self):
  f=audit_branch_assignment_gaps.scan_file(SOURCE_PATH,SOURCE_ROOT); t=[x for x in f if x.get("function")=="GetConnexionReseau" and x.get("name")=="connexion"]; self.assertEqual(t,[])
