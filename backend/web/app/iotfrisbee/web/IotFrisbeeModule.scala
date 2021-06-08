package iotfrisbee.web

import akka.actor.{ActorRef, ActorSystem}
import akka.cluster.pubsub.DistributedPubSub

import scala.concurrent.Future
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import iotfrisbee.database.catalog.DiskGolfBasketCatalog.DiskGolfBasketTable
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
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.DiskGolfTrackTable
import iotfrisbee.database.catalog.HardwareCatalog.HardwareTable
import iotfrisbee.database.catalog.HardwareMessageCatalog.HardwareMessageTable
import iotfrisbee.database.catalog.UserCatalog.UserTable
import iotfrisbee.database.catalog.DiskGolfDiskCatalog.DiskGolfDiskTable
import iotfrisbee.database.catalog.DiskGolfGameCatalog.DiskGolfGameTable
import iotfrisbee.database.catalog.DiskGolfGameStageCatalog.DiskGolfGameStageTable
import iotfrisbee.database.driver.DatabaseDriver.{JdbcDatabaseDriver, fromJdbcConfig, fromPlayDatabase}
import iotfrisbee.database.services._
import iotfrisbee.domain.IotFrisbeeConfig
import iotfrisbee.web.IotFrisbeeModule.prepareDatabaseForTest
import iotfrisbee.web.actors.CentralizedPubSubActor
import iotfrisbee.web.controllers._
import iotfrisbee.web.config.IotFrisbeeConfig._

class IotFrisbeeModule(context: Context)(implicit iort: IORuntime)
    extends BuiltInComponentsFromContext(context)
    with HttpFiltersComponents
    with EvolutionsComponents
    with SlickComponents
    with SlickEvolutionsComponents
    with ClusterShardingComponents {
  lazy val appConfig: IotFrisbeeConfig = context.initialConfiguration.get[IotFrisbeeConfig]("iotfrisbee")

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
  lazy val diskGolfTrackTable = new DiskGolfTrackTable(defaultDatabaseDriver)
  lazy val hardwareTable = new HardwareTable(defaultDatabaseDriver)
  lazy val hardwareMessageTable = new HardwareMessageTable(defaultDatabaseDriver)
  lazy val diskGolfDiskTable = new DiskGolfDiskTable(defaultDatabaseDriver)
  lazy val diskGolfBasketTable = new DiskGolfBasketTable(defaultDatabaseDriver)
  lazy val diskGolfGameTable = new DiskGolfGameTable(defaultDatabaseDriver)
  lazy val diskGolfGameStageTable = new DiskGolfGameStageTable(defaultDatabaseDriver)

  lazy val userService = new UserService[IO](userTable)
  lazy val diskGolfTrackService = new DiskGolfTrackService[IO](diskGolfTrackTable, userTable)
  lazy val hardwareService = new HardwareService[IO](hardwareTable, userTable)
  lazy val hardwareMessageService = new HardwareMessageService[IO](hardwareMessageTable, hardwareTable)
  lazy val diskGolfDiskService = new DiskGolfDiskService[IO](diskGolfDiskTable, diskGolfTrackTable, hardwareTable)
  lazy val diskGolfBasketService = new DiskGolfBasketService[IO](diskGolfBasketTable, diskGolfTrackTable, hardwareTable)
  lazy val diskGolfGameService = new DiskGolfGameService[IO](
    userTable,
    diskGolfTrackTable,
    diskGolfDiskTable,
    diskGolfBasketTable,
    diskGolfGameTable,
    diskGolfGameStageTable,
    hardwareTable,
  )

  lazy val homeController = new HomeController(
    controllerComponents,
    userService,
    diskGolfTrackService,
    hardwareService,
    hardwareMessageService,
    diskGolfDiskService,
    diskGolfBasketService,
  )
  lazy val userController = new UserController(controllerComponents, userService)
  lazy val diskGolfTrackController = new DiskGolfTrackController(controllerComponents, diskGolfTrackService)
  lazy val hardwareController = new HardwareController(controllerComponents, hardwareService)
  lazy val hardwareMessageController =
    new HardwareMessageController(controllerComponents, pubSubMediator, hardwareMessageService)
  lazy val diskGolfDiskController = new DiskGolfDiskController(controllerComponents, diskGolfDiskService)
  lazy val diskGolfBasketController = new DiskGolfBasketController(controllerComponents, diskGolfBasketService)
  lazy val diskGolfGameController = new DiskGolfGameController(controllerComponents, diskGolfGameService)

  lazy val basePrefix = "/api"
  lazy val v1Prefix = "/v1"
  lazy val router: Router =
    new IotFrisbeeRouter(
      homeController,
      userController,
      diskGolfTrackController,
      hardwareController,
      hardwareMessageController,
      diskGolfDiskController,
      diskGolfBasketController,
      diskGolfGameController,
    ).withPrefix(f"${basePrefix}${v1Prefix}")
}

object IotFrisbeeModule {
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