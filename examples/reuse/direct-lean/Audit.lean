import DirectReuse

open scoped ContDiff

set_option autoImplicit false

-- Read the elaborated interface and transitive axioms from this environment.
-- These commands are ordinary Lean inspection, not a Slean verification receipt.
#check @ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'
#print axioms ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'
#check @DirectReuse.energy_at_two_times
#print axioms DirectReuse.energy_at_two_times
