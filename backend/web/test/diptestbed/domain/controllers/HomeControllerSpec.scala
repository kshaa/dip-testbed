package diptestbed.domain.controllers

import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import io.circe._
import diptestbed.domain.controllers.HomeControllerSpec._
import diptestbed.domain.controllers.DIPTestbedSpec.exchangeJSON
import diptestbed.protocol._
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.controllers.HomeController
import diptestbed.web.DIPTestbedModule
import play.api.mvc.AnyContent

class HomeControllerSpec extends DIPTestbedSpec {
  lazy val module: DIPTestbedModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController

  "HomeController#status" - {
    "should be valid" in {
      getStatus(homeController).map(_.shouldEqual(Right(Success(ServiceStatus.empty))))
    }
  }
}

object HomeControllerSpec {
  def getStatus(
    homeController: HomeController,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[ServiceStatus]]] =
    exchangeJSON[AnyContent, Success[ServiceStatus]](homeController.status)
}
