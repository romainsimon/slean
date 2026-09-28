import ApplicationExample

#slean_export [DirectReuse.energy_at_two_times] to "_out/application-producer.json"
#slean_export [ApplicationExample.energy_with_obligation, ApplicationExample.energy_with_all_arguments]
  to "_out/application-consumer.json"
#slean_export_applications [ApplicationExample.energy_with_obligation, ApplicationExample.energy_with_all_arguments]
  to "_out/applications.json"
