ShapesDemo-matplotlib
===================
Reimplementation of RTI ShapesDemo with Connext Python API and matplotlib

Goals
-----
  Experiment with the PythonAPI
  Provide a richer scriptable way to startup Demos

Design Decisions
----------------
  Support both a simple command-line and a richer file-based configuration.
  Provide reasonable defaults with the ability to override.
  Meant to interoperate with not fully replace rtishapesdemo.
  Let a QoS file handle what it can.

ToDo
----
  Validate on non-Mac platforms, different screen sizes, numbers.
  Collect useful sets of instances / useCases into named scenarios.
  Add graphic indicator of: stopped publisher (?); the no publisher (X) is implemented
  Add more unittests
  Release packaging
