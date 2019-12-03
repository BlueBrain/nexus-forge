Feature: Store
  An interface representing what a data store should and could provide to
  the user and the other elements of the Knowledge Graph Forge.

  Scenario: The registration of a resource succeeds.
    Given A store instance.
    And A valid resource.
    When I register the resource. The printed report does not mention an error.
    Then The '_synchronized' status of the resource should be 'True'.
    And The store metadata of a resource should be '{'version': 1, 'deprecated': False}'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_register_one'.
    And The report should say that the operation success is 'True'.
    And The report should say that the error was 'None'.

  Scenario: The registration of resources succeeds.
    Given A store instance.
    And Valid resources.
    When I register the resources. The printed report does not mention an error.
    Then The '_synchronized' status of a resource should be 'True'.
    And The store metadata of a resource should be '{'version': 1, 'deprecated': False}'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_register_one'.
    And The report should say that the operation success is 'True'.
    And The report should say that the error was 'None'.

  Scenario: The registration of a resource fails.
    Given A store instance.
    And An already registered resource.
    When I register the resource. The printed report does mention an error: 'RegistrationError: resource should not be synchronized'.
    Then The '_synchronized' status of the resource should be 'False'.
    And The store metadata of a resource should be '{'version': 1, 'deprecated': False}'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_register_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'RegistrationError'.

  Scenario: The registration of resources fails.
    Given A store instance.
    And Already registered resources.
    When I register the resources. The printed report does mention an error: 'RegistrationError: resource should not be synchronized'.
    Then The '_synchronized' status of a resource should be 'False'.
    And The store metadata of a resource should be '{'version': 1, 'deprecated': False}'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_register_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'RegistrationError'.

  Scenario: An exception is raised during the registration of a resource.
    Given A store instance.
    And A valid resource.
    When I register the resource. An exception is raised. The printed report does mention an error: 'Exception: exception raised'.
    Then The '_synchronized' status of the resource should be 'False'.
    And The store metadata of a resource should be 'None'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_register_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'Exception'.

  Scenario: Modifying a synchronized resource sets its registration status to False.
    Given An already registered resource.
    When I modify the resource.
    Then The '_synchronized' status of the resource should be 'False'.
    And The store metadata of a resource should be '{'version': 1, 'deprecated': False}'.
