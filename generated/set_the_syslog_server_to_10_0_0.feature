@feature=set_the_syslog_server_to @layer=gui @layer=hardware @priority=p1 @ticket=DEMO-1
Feature: Set the syslog server to 10.0.0.5 in the management UI and verify it was applied on the device within 10 seconds.

  @smoke @environment=docker_demo
  Scenario: Set the syslog server to 10.0.0.5 in the management UI and verify it was applied on the device within 10 seconds.
    Given I am logged in to the management console
    When I set the syslog server to 10.0.0.5 in the management UI
    Then the device config file has syslog server set to 10.0.0.5 within 10 seconds
