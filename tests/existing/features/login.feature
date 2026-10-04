@feature=login @layer=gui @priority=p0 @ticket=DEMO-0
Feature: Management console login

  @smoke @environment=docker_demo
  Scenario: Admin can log in
    Given I am logged in to the management console
