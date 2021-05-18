package iotfrisbee.web

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.DiskGolfTrackTable
import iotfrisbee.database.catalog.UserCatalog.UserTable
import iotfrisbee.database.driver.DatabaseDriver.{JdbcDatabaseDriver, fromJdbcConfig, fromPlayDatabase}
import iotfrisbee.database.services.{DiskGolfTrackService, UserService}
import iotfrisbee.domain.IotFrisbeeConfig
import iotfrisbee.web.IotFrisbeeModule.prepareDatabaseForTest
import iotfrisbee.web.controllers.HomeController
import iotfrisbee.web.configloaders.IotFrisbeeConfig._
import play.api.ApplicationLoader.Context
import play.api._
import play.api.db.evolutions.ThisClassLoaderEvolutionsReader.evolutions
import play.api.db.{Database => PlayDatabase}
import play.api.db.evolutions.{Evolutions, EvolutionsComponents, SimpleEvolutionsReader}
import play.api.db.slick.evolutions.SlickEvolutionsComponents
import play.api.db.slick.{DbName, SlickComponents}
import play.api.routing.Router
import play.filters.HttpFiltersComponents
import slick.jdbc.{H2Profile, JdbcProfile}
import scala.concurrent.Future

class IotFrisbeeModule(context: Context)(implicit iort: IORuntime)
    extends BuiltInComponentsFromContext(context)
    with HttpFiltersComponents
    with EvolutionsComponents
    with SlickComponents
    with SlickEvolutionsComponents {

  lazy val appConfig: IotFrisbeeConfig = context.initialConfiguration.get[IotFrisbeeConfig]("iotfrisbee")

  lazy val defaultDatabaseDriver: JdbcDatabaseDriver = appConfig.testConfig.testName
    .map(testName => fromPlayDatabase(prepareDatabaseForTest(context, testName), H2Profile))
    .getOrElse(fromJdbcConfig(slickApi.dbConfig[JdbcProfile](DbName("default"))))

  lazy val userTable = new UserTable(defaultDatabaseDriver)
  lazy val diskGolfTrackTable = new DiskGolfTrackTable(defaultDatabaseDriver)

  lazy val userService = new UserService[IO](defaultDatabaseDriver, userTable)
  lazy val diskGolfTrackService =
    new DiskGolfTrackService[IO](defaultDatabaseDriver, diskGolfTrackTable)

  lazy val homeController =
    new HomeController(controllerComponents, userService, diskGolfTrackService)

  lazy val router: Router =
    new IotFrisbeeRouter(homeController)
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
