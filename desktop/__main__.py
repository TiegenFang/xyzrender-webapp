import multiprocessing

from .launcher import main


multiprocessing.freeze_support()
raise SystemExit(main())
