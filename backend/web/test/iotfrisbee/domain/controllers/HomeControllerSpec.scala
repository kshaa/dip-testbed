package iotfrisbee.domain.controllers

import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import io.circe._
import iotfrisbee.domain.controllers.HomeControllerSpec._
import iotfrisbee.domain.controllers.IotFrisbeeSpec.exchangeJSON
import iotfrisbee.protocol.Codecs.Http._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.web.controllers.HomeController
import iotfrisbee.protocol.messages.home.ServiceStatus
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.web.IotFrisbeeModule
import play.api.mvc.AnyContent

class HomeControllerSpec extends IotFrisbeeSpec {
  lazy val module: IotFrisbeeModule = module()
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
