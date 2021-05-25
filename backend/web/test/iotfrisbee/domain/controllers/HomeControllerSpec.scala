package iotfrisbee.domain.controllers

import scala.concurrent.Future
import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import io.circe._
import play.api.test.{FakeRequest, Helpers}
import io.circe.parser._
import iotfrisbee.domain.controllers.HomeControllerSpec._
import iotfrisbee.protocol.Codecs.Http._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.web.controllers.HomeController
import iotfrisbee.web.iocontrols.PipelineOps._
import iotfrisbee.protocol.messages.home.ServiceStatus
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.web.IotFrisbeeModule

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
  )(implicit timeout: Timeout): IO[Either[Error, Success[ServiceStatus]]] =
    homeController
      .status()
      .apply(FakeRequest())
      .asIO
      .map(x => Helpers.contentAsString(Future.successful(x)))
      .map(x => decode[Success[ServiceStatus]](x))
}
