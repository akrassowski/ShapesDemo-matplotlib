# shapes-matplotlib
Reimplementation of RTI ShapesDemo with PythonAPI and matplotlib

Goals:
  Experiment with the PythonAPI
  Provide a richer scriptable way to startup Demos

Design Decisions:
  Support either a simple command-line or file-based configuration.
  Provide reasonable defaults with the ability to override.
  Meant to interoperate not replace rtishapesdemo.
  Let a QoS file handle what it can.

ToDo:
  Validate on non-Mac platforms.
  Collect useful sets of instances / useCases into named settings (x4, x6, x8, etc.)
  Documentation by example
  Add graphic indicator of: stopped publisher (?), no publisher (X)
  Add more unittests
  Release packaging
