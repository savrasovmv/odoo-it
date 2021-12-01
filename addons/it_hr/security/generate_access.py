spisok = []
# spisok.append(['adbook.branch','', 1])
spisok.append(['hr.recruitment_doc','', 1])
spisok.append(['hr.termination_doc','', 1])
spisok.append(['hr.vacation_doc','', 1])
spisok.append(['hr.trip_doc','', 1])
spisok.append(['hr.sick_leave_doc','', 1])
spisok.append(['hr.transfer_doc','', 1])



spisok_read = []
# spisok_read.append(['adbook.branch',''])
# spisok_read.append(['adbook.department',''])
# spisok_read.append(['adbook.employer',''])






print("id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink")
for name in spisok:
	class_name = name[0].replace('.','_')
	modul_name = ''
	
	if len(name[1])>0:
		modul_name = name[1] + '.'
	print('access_%(class_name)s_manager,%(name)s,%(modul_name)smodel_%(class_name)s,hr.group_hr_manager,1,1,1,1' % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
	if name[2]>0:
		print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,hr.group_hr_user,1,0,0,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
for name in spisok_read:
	class_name = name[0].replace('.','_')
	modul_name = ''
	
	if len(name[1])>0:
		modul_name = name[1] + '.'
	
	print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,base.group_user,1,0,0,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
	print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,base.group_portal,1,0,0,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
