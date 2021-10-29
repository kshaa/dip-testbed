package diptestbed.web

import akka.actor.{ActorRef, ActorSystem}
import akka.cluster.pubsub.DistributedPubSub
import scala.concurrent.Future
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import play.api.ApplicationLoader.Context
import play.api._
import play.api.cluster.sharding.typed.ClusterShardingComponents
import play.api.db.evolutions.ThisClassLoaderEvolutionsReader.evolutions
import play.api.db.{Database => PlayDatabase}
import play.api.db.evolutions.{Evolutions, EvolutionsComponents, SimpleEvolutionsReader}
import play.api.db.slick.evolutions.SlickEvolutionsComponents
import play.api.db.slick.{DbName, SlickComponents}
import play.api.routing.Router
import play.filters.HttpFiltersComponents
import slick.jdbc.{H2Profile, JdbcProfile}
import diptestbed.database.catalog.HardwareCatalog.HardwareTable
import diptestbed.database.catalog.SoftwareCatalog.SoftwareTable
import diptestbed.database.catalog.UserCatalog.UserTable
import diptestbed.database.driver.DatabaseDriver.{JdbcDatabaseDriver, fromJdbcConfig, fromPlayDatabase}
import diptestbed.database.services._
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.DIPTestbedModuleHelper.prepareDatabaseForTest
import diptestbed.web.actors.CentralizedPubSubActor
import diptestbed.web.controllers._
import diptestbed.web.config.DIPTestbedConfig._

class DIPTestbedModule(context: Context)(implicit iort: IORuntime)
    extends BuiltInComponentsFromContext(context)
    with HttpFiltersComponents
    with EvolutionsComponents
    with SlickComponents
    with SlickEvolutionsComponents
    with ClusterShardingComponents {
  lazy val appConfig: DIPTestbedConfig = context.initialConfiguration.get[DIPTestbedConfig]("diptestbed")

  lazy implicit val implicitActorSystem: ActorSystem = actorSystem
  lazy val pubSubMediator: ActorRef = if (appConfig.clusterized) {
    DistributedPubSub(actorSystem).mediator
  } else {
    actorSystem.actorOf(CentralizedPubSubActor.props)
  }

  lazy val defaultDatabaseDriver: JdbcDatabaseDriver = appConfig.testConfig.testName
    .map(testName => fromPlayDatabase(prepareDatabaseForTest(context, testName), H2Profile))
    .getOrElse(fromJdbcConfig(slickApi.dbConfig[JdbcProfile](DbName("default"))))

  lazy val userTable = new UserTable(defaultDatabaseDriver)
  lazy val hardwareTable = new HardwareTable(defaultDatabaseDriver)
  lazy val softwareTable = new SoftwareTable(defaultDatabaseDriver)

  lazy val userService = new UserService[IO](userTable)
  lazy val hardwareService = new HardwareService[IO](hardwareTable, userTable)
  lazy val softwareService = new SoftwareService[IO](softwareTable, userTable)

  lazy val homeController = new HomeController(
    controllerComponents,
    userService,
    hardwareService,
    softwareService,
  )
  lazy val userController = new UserController(controllerComponents, userService)
  lazy val hardwareController =
    new HardwareController(controllerComponents, pubSubMediator, hardwareService, userService)
  lazy val softwareController =
    new SoftwareController(controllerComponents, softwareService, userService)

  lazy val basePrefix = "/api"
  lazy val v1Prefix = "/v1"
  lazy val router: Router =
    new DIPTestbedRouter(
      homeController,
      userController,
      hardwareController,
      softwareController,
    ).withPrefix(f"${basePrefix}${v1Prefix}")
}

object DIPTestbedModuleHelper {
  def prepareDatabaseForTest(context: Context, testName: String): PlayDatabase = {
    // Create test database
    lazy val defaultTestDatabaseName = f"default-test-${testName}"
    lazy val defaultTestPlayDb: PlayDatabase =
      play.api.db.Databases.inMemory(
        name = defaultTestDatabaseName,
        urlOptions = Map(
          "MODE" -> "PostgreSQL",
          "DB_CLOSE_DELAY" -> "-1",
        ),
        config = Map(
          "logStatements" -> true,
        ),
      )

    // Run evolutions
    val defaultEvolutions = evolutions("default")
    Evolutions.applyEvolutions(
      defaultTestPlayDb,
      new SimpleEvolutionsReader(Map(defaultTestDatabaseName -> defaultEvolutions)),
    )

    // Shutdown database after test
    context.lifecycle.addStopHook(() => {
      Future.successful(defaultTestPlayDb.shutdown())
    })

    // Return database
    defaultTestPlayDb
  }
}
