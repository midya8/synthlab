from .__main__ import main as transport
from .teaching import teaching_atlas,verify_teaching

def main():return transport(teaching_atlas,verify_teaching,'Exact finite target-distinguishing-set atlas and independent verification')
if __name__=='__main__':raise SystemExit(main())
