import random
import copy
import numpy as np
import theano as T
import theano.tensor as tt
from clean_steves_data import *
import re
import editdistance
from math import log, exp
import math

matching_set = [('(', ')'), ('[', ']'), (')', '('), (']','[')]
open_set = ["(", "["]
closed_set = [")", "]"]
all_p = ['(','[',']',')']


def print_star(*args):
    if len(args) > 0:
        for arg in args:
            print arg
        print "*" * 100
        print



def make_lists(prims=['(','[',']',')'], 
               resps=[""], length=4):

    if ((not len(resps) == 0) and 
               len(resps[0]) == length):
        return resps
    else:
        new_resps = []
        for r in resps:
            for p in prims:
                new_resp = r + p
                new_resps.append(new_resp)

        return make_lists(prims,new_resps,length)

def get_hyps_gen(hyps):
    r_dct = {}
    for hyp in hyps:
        hyp_gen = get_hyp_gen(hyp, 
            copy.copy(all_p),
            copy.copy(open_set), 
            copy.copy(closed_set))

        r_dct[hyp] = copy.deepcopy(hyp_gen)
    return r_dct




def filter_hyps(out_hyps, thresh=2.0, rem_dup=False):
	keep = {}
	kept = []
	lx = lambda x: -(x.count("(") + x.count("[") + 
					x.count("]") + x.count(")") + x.count("M") )
	for h in sorted(out_hyps.keys(), key=lx):
		badness = 0.0
		ext = sorted([k for k in out_hyps[h]])
		for k in out_hyps[h]:
			badness += float(k.count("*")) * out_hyps[h][k]


		if ((badness < thresh) and
			((not rem_dup) or 
				(ext not in kept))):

			keep[h] = out_hyps[h]
			kept.append(copy.deepcopy(ext))


	return keep




def lst_format_data(paren_lst,  *args):

    all_resps = []
    assignments = []
    for a in xrange(len(args)):

        for part in args[a]:
            resps = []

            for i in xrange(len(paren_lst)):
                use_paren = tuple(paren_lst[i])

                if use_paren in part:
                    resps.append(part[use_paren])

                else:
                    resps.append(0)
            assignments.append(a)
            all_resps.append(copy.deepcopy(np.array(resps)))
    return np.array(all_resps), np.array(assignments)



def format_algs(paren_lst, algs, sm=1e-2, pref=0.5):
    out = []
    for which in algs:
        alg =algs[which]
        resp = [0.0 for _ in xrange(len(paren_lst))]
        for i in xrange(len(paren_lst)):
            for alg_paren in alg:
                bias_start = (alg_paren[0] == "(")
                bias = bias_start * pref + (1 - bias_start) * (1 - pref)
                hd = editdistance.eval(alg_paren, paren_lst[i])
                #hd = hamming_distance(alg_paren, paren_lst[i]) 
                add = sm ** hd
                if  sm > 0:
                    add = sm ** hd #+ log(bias, sm)

                resp[i] +=  add
                #if (resp[i] == None or 
                   # (resp[i] < 0.2**hd)):
                    #resp[i] = 0.2**hd
        resp = np.array(resp)
        sum_r = np.sum(resp)
        normed = resp * (1.0/sum_r)
        out.append(normed)
    return np.array(out)





def hamming_distance(true_paren, comp_paren):
    assert(len(true_paren) == len(comp_paren))

    dif = 0
    for z in xrange(len(true_paren)):
        if true_paren[z] != comp_paren[z]:
            dif += 1

    return dif


def group_vars(vars,  group_by):
    #returns a dictionary with
    #key=variable_type, value = tuple(names, values)


    names = list(vars.axes[0])
    values = list(vars)

    dct = {}

    for n in xrange(len(names)):
        name = names[n]
        for g in group_by:
            if g in name:
                if g not in dct:
                    dct[g] = []
                dct[g].append(n)

    ret = {}
    for d in dct.keys():
        min_i = min(dct[d])
        max_i = max(dct[d])
        ret[d] = (names[min_i:max_i+1], values[min_i:max_i+1])

    return ret

        
def get_algs_of_type(algorithms):
    #classifies algorithm type by
    #recursive (CE only), crossing (CE + CR)
    # or tail recursive (TR)
    CE = ["([])", "[()]"]
    CR = ["[(])", "([)]"]
    TR = ["[]()", "()[]"]
    types = []

    for a in algorithms:
        alg =algorithms[a]
        p_CE = 0.0
        p_CR = 0.0
        p_TR = 0.0
        p_OTHER = 0.0
        for paren_type in alg:
            if paren_type in CE:
                p_CE += alg[paren_type]
            elif paren_type in CR:
                p_CR += alg[paren_type]
            elif paren_type in TR:
                p_TR += alg[paren_type]
            else:
                p_OTHER += alg[paren_type]

        if p_CE == 1.0:
            types.append("Recursive")
        elif p_CE == 0.5 and p_CR == 0.5:
            types.append("Crossing")
        elif p_TR == 1.0:
            types.append("Tail")
        else:
            types.append("Other")

    return types

def amount_alg_type(alg_types, values_lst, which_type = "Recursive"): 
    #returns how much of X algorithm each participant or group is
    #(values is list of lists of floats)
    assert(len(values_lst) > 0)
    amounts = []
    for values in values_lst:
        assert(len(alg_types) == len(values))
        amount = 0.0
        for a in xrange(len(alg_types)):
            alg_type = alg_types[a]
            value = values[a]
            if alg_type == which_type:
                amount += value

        amounts.append(amount)

    return amounts

def output_alphas(names, means, sds, file):
    o = "who,mean,sds\n"
    for i in xrange(len(names)):
        name = names[i]
        mean = means[i]
        sd = sds[i]
        o += "%s,%f,%f\n" % (name, mean, sd)

    f = open(file, "w+")
    f.write(o)
    f.close()

def output_betas(names, group_alg, group_sds, order, alg_names, alg_types, file):
    o = "who, alg_name, alg_type, val,sds\n"
    for i in xrange(len(group_alg)):
        who = order[i]
        vals= group_alg[i]
        sds = group_sds[i]
        for j in xrange(len(vals)):
            alg_name = alg_names[j]
            alg_type =alg_types[j]
            val = vals[j]
            sd = sds[j]
            o += "%s,%s,%s,%f,%f\n" % (who,alg_name,alg_type,val,sd)

    f =open(file, "w+")
    f.write(o)
    f.close()


def output_thetas(names, part_alg, part_sds, order, 
        alg_names, alg_types, file):
    o = "who,id,alg_name,alg_type,val,sds\n"
    for i in xrange(len(part_alg)):
        who = order[i]
        vals= part_alg[i]
        sds = part_sds[i]

        for j in xrange(len(vals)):
            alg_name = alg_names[j]
            alg_type =alg_types[j]
            alg_sd = sds[j]
            val = vals[j]
            o += ("%s, %d, %s, %s, %f, %f\n" % 
                (who,i,alg_name,alg_type,val,alg_sd))

    f =open(file, "w+")
    f.write(o)
    f.close()

def output_full_alpha_noise(trace, which, name,added=[],thin=1, out="noise_full.csv"):
    o = "sample,thin_sample,who,part,digits,value\n"
    noise_sum = [0.0 for _ in xrange(len(trace[0][which]))]
    for m in xrange(len(trace)):

        #assert(len(trace[m][which]) == len(names))
        for n in xrange(len(trace[m][which])):
            trial = m*thin
            #name = names[n]

            forward_dig="None"
            if len(added) > 0:
                forward_dig = added[n]

            val = trace[m][which][n] 

            noise_sum[n] += trace[m][which][n]/float(len(trace))

            o += ("%d,%d,%s,%d,%s,%f\n" % (m, trial, name, n,forward_dig, val))

    f = open(out, "w+")
    f.write(o)
    f.close()
    return noise_sum


def output_full_beta(trace, which, group,names,thin, out, added=[]):
    o = "sample,thin_sample,who,which,forward,value\n"
    for m1 in xrange(0,len(trace), thin):
        trial = m1
        #trial = m1 * thin
        #assert(len(trace[m1][which]) == len(groups))

            #group = groups[m2]
        forward =  "None"

        for n in xrange(len(trace[m1][which])):

            name = names[n]
            val = trace[m1][which][n]

            o += ("%d,%d,%s,%s,%s,%f\n" % (m1, trial, str(group), 
                                            str(name),forward, val))

    f = open(out, "w+")
    f.write(o)
    f.close()



def output_full_theta(trace, which, group,names,thin, out, added=[]):
    o = "sample,thin_sample,who,part,which,forward,value\n"
    for m1 in xrange(0,len(trace), thin):
        trial = m1

        #trial = m1 * thin
        #assert(len(trace[m1][which]) == len(groups))
        for m2 in xrange(len(trace[m1][which])):
            forward =  "None"
            if len(added) > 0:
                forward = str(added[m2])
            #assert(len(trace[m1][which][m2]) == len(names))
            for n in xrange(len(trace[m1][which][m2])):

                name = names[n]
                val = trace[m1][which][m2][n]

                o += ("%d,%d,%s,%d,%s,%s,%f\n" % (m1, trial, str(group), 
                                                m2, str(name),forward, val))

    f = open(out, "w+")
    f.write(o)
    f.close()


def get_0_columns(arr):
    assert(len(arr) > 0)
    column_0s = set()
    tp_arr = arr.transpose()

    assert(len(tp_arr[0]) > 0)
    for a in xrange(len(arr[0])):
        if sum(tp_arr[a]) == 0:
            column_0s.add(a)

    return column_0s



def store_hds_old(paren_lst, algs):
    out = []
    for which in algs:
        alg =algs[which]
        hds_list = []

        for i in xrange(len(paren_lst)):
            hds = []
            for alg_paren in alg:
                #hd = hamming_distance(alg_paren, paren_lst[i])
                hd = editdistance.eval(alg_paren, paren_lst[i])
                hds.append(hd)
            #hds = np.array(hds)
            #hds_t = tt.as_tensor(hds)
            hds_list.append(copy.deepcopy(hds))

        out.append(copy.deepcopy(tt.as_tensor(hds_list)))

    return out



def store_hds(paren_lst, algs):
    out = []
    size = []
    max_hd = 0
    for which in algs:
        alg =algs[which]
        hds_list = []

        for i in xrange(len(paren_lst)):
            hds = []
            for alg_paren in alg:
                #hd = hamming_distance(alg_paren, paren_lst[i])
                hd = editdistance.eval(alg_paren, paren_lst[i])
                hds.append(hd)                
            #hds = np.array(hds)
            #hds_t = tt.as_tensor(hds)
            hds_list.append(copy.deepcopy(hds))
        if len(hds_list[0]) > max_hd:
            max_hd = len(hds_list[0])
        out.append(copy.deepcopy(hds_list))

    ret = []
    for o in out:
        tmp = []
        for z in o:
            new_z = copy.deepcopy(z)
            if len(z) != max_hd:
                for _ in xrange(max_hd - len(z)):
                    new_z.append(0)
            tmp.append(copy.deepcopy(new_z))
        ret.append((copy.deepcopy(tmp)))

    return np.array(ret), max_hd




def format_algs_theano(hds, sm):


    #ps = tt.pow(sm,hds[0]) + tt.pow(sm,hds[1]) + tt.pow(sm,hds[2]) + tt.pow(sm,hds[3])
    #ps = tt.sum(ps,axis=1)

    ps = [tt.pow(sm, o).sum(axis=1) for o in hds]
    #ps = tt.scan(fn=lambda sm,o : tt.pow(sm,o).sum(axis=1),
               #     outputs_info=hds)
    #out = [p * (1.0/p.sum()) for p in ps]
   # out_tens = tt.stack(out)
    #return out_tens

    return ps
    #return tt.stack(ps)


        

def format_algs_theano_bypart(hds, sms, total_parts=46,n_algs=9, max_hd=4):
    x = tt.dtensor3('x')
    y=tt.dtensor3('y')

    ass = np.array([i/(65 * 4 * 9) for i in xrange(9 * 65 * 4 * 46)])
   # for i in xrange(46):
      #  print i, list(ass).count(i)

    sms = sms[ass].reshape((46, 9,65,4))


    x = tt.pow(sms, hds)

    x = tt.sum(x, axis=3)

    return x

def get_hyps_gen_noise_N(hyps,mem_noise):
    r_dct = {}
    for hyp in hyps:
        hyp_gen = get_hyp_gen_noise_N(hyp, 
            set(copy.copy(all_p)),
            set(copy.copy(open_set)), 
            set(copy.copy(closed_set)),mem_noise)

        r_dct[hyp] = copy.deepcopy(hyp_gen)
    return r_dct




def store_start_p(paren_lst, n=1, lst = ["(", ")"]):
    out = []
    for which in paren_lst:
        if which[0] in lst:
            out.append(1)
        else:
            out.append(0)
    ret = np.array(out * n)
    ret = ret.reshape((n, len(paren_lst)))
    return ret



#def get_distribution_parens(parts)


def get_hyp_gen(hyp, available,
                 open_available, 
                 closed_available, 
                 sofar=""):


    def find_match(m, available):
        for r in available:
            if (m, r) in matching_set or (r, m) in matching_set:
                return r
        return None
    
    if len(hyp) == 0:
        return {"":1.0}

    else:
        h = hyp[0]
        poss = {}
        if h in "([])" and h in available:
            poss[h] = 1.0

        elif h == "O" and len(open_available)>0:
            for o in open_available:
                poss[o] = 1/float(len(open_available))

        elif h == "C" and len(closed_available)>0:
            for o in closed_available:
                poss[o] = 1/float(len(closed_available))

        elif h == "M" and len(available) > 0:
            for s in sofar[::-1]:
                match = find_match(s, available)
                if ((match in closed_available) or
                         (match in open_available)):
                    poss[match] = 1.0
                    break



        if len(poss.keys()) == 0:
            poss["*"] = 1.0


        ret_dcts = {}
        for key in poss:
            new_av = copy.copy(available)
            new_opav = copy.copy(open_available)
            new_clav = copy.copy(closed_available)
            new_sofar = sofar + key
            if key in new_av:
                new_av.remove(key)
                if key in new_opav:
                    new_opav.remove(key)
                else:
                    new_clav.remove(key)

            from_here = get_hyp_gen(hyp[1:], 
                                    new_av,
                                    new_opav,
                                    new_clav,
                                    new_sofar)
            prob_key = poss[key]
            for k in from_here:
                prob_here =from_here[k]
                if key + k not in ret_dcts:
                    ret_dcts[key + k] = 0.0
                ret_dcts[key+k] += prob_here * prob_key

        return ret_dcts

if __name__ == "__main__":
    print get_hyps_gen(["CCMM"])