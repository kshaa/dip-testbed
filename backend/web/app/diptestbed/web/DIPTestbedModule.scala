package diptestbed.web

import akka.actor.{ActorRef, ActorSystem}
import akka.cluster.pubsub.DistributedPubSub

import scala.concurrent.Future
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import play.api.ApplicationLoader.Context
import play.api.BuiltInComponentsFromContext
import controllers.{Assets, AssetsComponents, AssetsConfiguration, AssetsMetadataProvider, DefaultAssetsMetadata}
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
import diptestbed.web.control._
import diptestbed.web.config.DIPTestbedConfig._

class DIPTestbedModule(context: Context)(implicit iort: IORuntime)
    extends BuiltInComponentsFromContext(context)
    with HttpFiltersComponents
    with EvolutionsComponents
    with SlickComponents
    with SlickEvolutionsComponents
    with ClusterShardingComponents {
  lazy val appConfig: DIPTestbedConfig = configuration.get[DIPTestbedConfig]("diptestbed")

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

  lazy val apiHomeController = new ApiHomeController(
    controllerComponents,
    userService,
    hardwareService,
    softwareService,
  )
  lazy val apiUserController = new ApiUserController(controllerComponents, userService)
  lazy val apiHardwareController =
    new ApiHardwareController(controllerComponents, pubSubMediator, hardwareService, userService)
  lazy val apiSoftwareController =
    new ApiSoftwareController(controllerComponents, softwareService, userService)

  lazy val apiRouter = new APIRouter(
    apiHomeController,
    apiUserController,
    apiHardwareController,
    apiSoftwareController
  )

  lazy val assetsConfiguration: AssetsConfiguration =
    AssetsConfiguration.fromConfiguration(configuration, environment.mode)
  lazy val assetsMetadata: DefaultAssetsMetadata =
    new AssetsMetadataProvider(environment, assetsConfiguration, fileMimeTypes, applicationLifecycle).get
  lazy val assets = new Assets(httpErrorHandler, assetsMetadata)
  lazy val assetsRouter = new AssetsRouter(assets)

  lazy val appHomeController = new AppHomeController(
    appConfig,
    controllerComponents
  )

  lazy val appRouter = new AppRouter(
    assets,
    appHomeController
  )

  lazy val redirectRouter = new RedirectRouter(appHomeController)

  lazy val router: Router =
    new DIPTestbedRouter(
      apiRouter,
      appConfig.withBase(appConfig.withVersionApiPrefix("v1")),
      assetsRouter,
      appConfig.withBase(appConfig.assetsPrefix),
      appRouter,
      appConfig.withBase(appConfig.appPrefix),
      redirectRouter
    )
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
