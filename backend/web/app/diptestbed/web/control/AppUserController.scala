package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{SoftwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, User, UserId}
import diptestbed.web.ioControls.IOController
import play.api.data.Form
import play.api.data.Forms.{boolean, optional, text, tuple}
import play.api.i18n.Messages
import play.api.mvc._

import java.util.UUID
import scala.util.Try

class AppUserController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO]
)(implicit
  iort: IORuntime,
  messages: Messages
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  implicit val ac: DIPTestbedConfig = appConfig

  def setPermissions(
    userUUID: String,
    isManager: Boolean,
    isLabOwner: Boolean,
    isDeveloper: Boolean
  ): Boolean = {
    println(isManager, isLabOwner, isDeveloper)
    val userId = Try(UUID.fromString(userUUID)).toOption.map(UserId)
    userId.traverse(id =>
      userService.setPermissions(id, isManager, isLabOwner, isDeveloper)
        .map(x => x.toOption.isDefined)).map(_.getOrElse(false)).unsafeRunSync()
  }

  val permissionsForm: Form[(String, Boolean, Boolean, Boolean)] = Form[(String, Boolean, Boolean, Boolean)](
    tuple(
      "user_id" -> text,
      "is_manager" -> optional(text).transform(_.contains("on"), if (_) Some("on") else None),
      "is_lab_owner" -> optional(text).transform(_.contains("on"), if (_) Some("on") else None),
      "is_developer" -> optional(text).transform(_.contains("on"), if (_) Some("on") else None),
    ) verifying ("Failed to change permissions", {
      case (userId, isManager, isLabOwner, isDeveloper) =>
        println(userId, isManager, isLabOwner, isDeveloper)
        setPermissions(userId, isManager, isLabOwner, isDeveloper)
    })
  )

  def users(requester: User): IO[List[User]] = userService.getUsers(Some(requester))
    .map(_.toOption.sequence.flatten.toList.filter(_ => requester.isManager))

  def list: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        Ok(diptestbed.web.views.html.userList(
          appConfig, Some(user), users(user).unsafeRunSync(), permissionsForm))
      }.unsafeRunSync()
    }

  def permissionsRequest: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        if (!user.isManager) {
          val formWithManagerError = permissionsForm.withGlobalError("Manager permission required")
          BadRequest(diptestbed.web.views.html.userList(
            appConfig, Some(user), users(user).unsafeRunSync(), formWithManagerError))
        } else {
          permissionsForm.bindFromRequest.fold(
            formWithErrors => BadRequest(diptestbed.web.views.html.userList(
              appConfig, Some(user), users(user).unsafeRunSync(), formWithErrors)),
            _ =>
              Ok(diptestbed.web.views.html.userList(
                appConfig, Some(user), users(user).unsafeRunSync(), permissionsForm))
          )
        }
      }.unsafeRunSync()
    }

}
