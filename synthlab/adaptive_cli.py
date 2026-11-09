from .__main__ import main as transport
from .adaptive import adaptive_atlas,verify_adaptive

def main():return transport(adaptive_atlas,verify_adaptive,'Exact finite remaining-query minimax atlas and independent verification',verify_cap=32*1024*1024)
if __name__=='__main__':raise SystemExit(main())
