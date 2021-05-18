package iotfrisbee.domain.controllers

import cats.effect.IO
import iotfrisbee.web.controllers.HomeController
import play.api.test.{FakeRequest, Helpers}

import scala.concurrent.Future

class HomeController2Spec extends IotFrisbeeSpec {
  lazy val controller: HomeController = module.homeController
  "Home2#index" - {
    "should be valid" in {
      IO.fromFuture(IO(controller.status().apply(FakeRequest())))
        .map(x => Helpers.contentAsString(Future.successful(x)))
        .map(x => x.shouldEqual("2"))
    }
  }
}
