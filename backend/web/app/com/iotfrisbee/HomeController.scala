package com.iotfrisbee

import controllers.AssetsFinder
import javax.inject._
import play.api.mvc._

@Singleton
class HomeController @Inject() (cc: ControllerComponents)(implicit
    assetsFinder: AssetsFinder
) extends AbstractController(cc) {

  def index: Action[AnyContent] =
    Action {
      Ok("Hello world.")
    }

}
