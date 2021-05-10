package com.iotfrisbee.controllers

import cats.effect.IO
import cats.effect.unsafe.implicits.global
import com.google.inject.Inject
import com.iotfrisbee.services.{DiskGolfTrackService, UserService}
import controllers.AssetsFinder
import play.api.mvc._
import javax.inject.Singleton

import scala.concurrent.ExecutionContext

@Singleton
class HomeController @Inject() (
    userService: UserService,
    diskGolfTrackService: DiskGolfTrackService,
    cc: ControllerComponents,
)(implicit
    assetsFinder: AssetsFinder,
    ec: ExecutionContext,
) extends AbstractController(cc) {

  def index: Action[AnyContent] =
    Action {
      Ok("Hello")
    }

  def userCount: Action[AnyContent] =
    Action.async { implicit request =>
      userService
        .countUsers()
        .map(_.toString)
        .map(Ok(_))
        .unsafeToFuture()
    }

  def diskGolfTrackCount: Action[AnyContent] =
    Action.async { implicit request =>
      diskGolfTrackService
        .countDiskGolfTracks()
        .map(_.toString)
        .map(Ok(_))
        .unsafeToFuture()
    }
}
